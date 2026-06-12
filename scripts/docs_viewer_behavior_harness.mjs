#!/usr/bin/env node
// Dependency-free behavioral harness for the actual docs viewer renderer.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'docs', 'viewer.js'), 'utf8');
const MALICIOUS_MARKDOWN = `# Security test

<script>globalThis.viewerPwned = true</script>

<img src=x onerror="globalThis.viewerPwned = true">

[javascript link](javascript:globalThis.viewerPwned=true)

[external link](https://example.com/?q="onmouseover="alert(1))

[local doc](./completion-contract.md)

\`\`\`html
<script>globalThis.viewerPwned = true</script>
\`\`\`
`;

class FakeElement {
  constructor(tag = 'div') {
    this.tag = tag;
    this.textContent = '';
    this.innerHTML = '';
    this.href = '';
    this.children = [];
    this.attributes = new Map();
  }

  append(...children) {
    this.children.push(...children);
  }

  replaceChildren(...children) {
    this.children = children;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }
}

const elements = new Map([
  ['doc-title', new FakeElement()],
  ['doc-meta', new FakeElement()],
  ['doc-body', new FakeElement()],
  ['doc-list', new FakeElement()],
  ['docs-home-link', new FakeElement('a')],
  ['github-link', new FakeElement('a')],
]);

const document = {
  title: '',
  querySelector(selector) {
    return elements.get(selector.replace(/^#/, '')) || null;
  },
  createElement(tag) {
    return new FakeElement(tag);
  },
  createDocumentFragment() {
    return new FakeElement('fragment');
  },
};
const window = {
  location: { hash: '#completion-contract.md' },
  addEventListener() {},
  setTimeout,
  clearTimeout,
};
const fetch = async () => ({
  ok: true,
  async text() {
    return MALICIOUS_MARKDOWN;
  },
});
const context = vm.createContext({
  console,
  document,
  window,
  fetch,
  AbortController,
  TextEncoder,
  URLSearchParams,
  decodeURIComponent,
  encodeURIComponent,
  Date,
  RegExp,
  Error,
  Object,
  Array,
  String,
  Number,
  Boolean,
  JSON,
  Math,
});

vm.runInContext(SOURCE, context, { filename: 'viewer.js' });
await new Promise((resolve) => setTimeout(resolve, 0));

const rendered = elements.get('doc-body').innerHTML;
assert.match(rendered, /&lt;script&gt;globalThis\.viewerPwned = true&lt;\/script&gt;/);
assert.match(rendered, /&lt;img src=x onerror=&quot;globalThis\.viewerPwned = true&quot;&gt;/);
assert.doesNotMatch(rendered, /<script|<img|<[^>]+\sonerror\s*=|href="javascript:/i);
assert.match(rendered, /<code>javascript link<\/code>/);
assert.match(rendered, /target="_blank" rel="noopener noreferrer"/);
assert.match(rendered, /href="#completion-contract\.md"/);
assert.equal(context.viewerPwned, undefined);
assert.equal(elements.get('github-link').href, 'https://github.com/Anstrays/arc-mcp-builder-assistant/blob/main/docs/completion-contract.md');

console.log('docs viewer behavior harness passed: malicious HTML/URLs escaped, safe external/local links preserved');

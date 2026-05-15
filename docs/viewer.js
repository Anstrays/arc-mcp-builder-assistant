const DOCS = [
  ['arc-mcp-setup.md', 'MCP setup'],
  ['arc-docs-map.md', 'Arc docs map'],
  ['deploy-contracts-arc.md', 'Deploy contracts on Arc'],
  ['builder-workflows.md', 'Builder workflows'],
  ['payment-intent-demo.md', 'Payment-intent demo spec'],
  ['prompt-library.md', 'Prompt library'],
  ['agent-identity-erc8004.md', 'Agent identity notes'],
  ['arc-builder-readiness-checklist.md', 'Builder readiness checklist'],
  ['agent-commerce-use-cases.md', 'Agent commerce use cases'],
  ['job-escrow-demo.md', 'Job escrow demo'],
  ['mcp-query-examples.md', 'MCP query examples'],
  ['arc-house-submission.md', 'Arc House submission draft'],
];

const allowedDocs = new Map(DOCS);
const docTitle = document.querySelector('#doc-title');
const docMeta = document.querySelector('#doc-meta');
const docBody = document.querySelector('#doc-body');
const docList = document.querySelector('#doc-list');
const rawLink = document.querySelector('#raw-link');
const githubLink = document.querySelector('#github-link');

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function currentDoc() {
  const fromHash = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim();
  return allowedDocs.has(fromHash) ? fromHash : DOCS[0][0];
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[`*_()[\]#:.]/g, '')
    .replace(/[^a-z0-9а-яё]+/gi, '-')
    .replace(/^-+|-+$/g, '') || 'section';
}

function inlineMarkdown(line) {
  let html = escapeHtml(line);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, text, href) => {
    const safeText = escapeHtml(text);
    const cleanHref = String(href).trim();
    if (/^(https?:|mailto:|tel:)/i.test(cleanHref)) {
      return `<a href="${escapeHtml(cleanHref)}" target="_blank" rel="noopener noreferrer">${safeText}</a>`;
    }
    const withoutFragment = cleanHref.split('#', 1)[0];
    if (allowedDocs.has(withoutFragment)) {
      return `<a href="#${encodeURIComponent(withoutFragment)}">${safeText}</a>`;
    }
    return `<code>${safeText}</code>`;
  });
  return html;
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const html = [];
  let inCode = false;
  let code = [];
  let inList = false;
  let listType = '';
  let paragraph = [];

  function closeParagraph() {
    if (paragraph.length) {
      html.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  }

  function closeList() {
    if (inList) {
      html.push(`</${listType}>`);
      inList = false;
      listType = '';
    }
  }

  function closeCode() {
    if (inCode) {
      html.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      inCode = false;
      code = [];
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.replace(/\s+$/, '');
    if (line.startsWith('```')) {
      if (inCode) {
        closeCode();
      } else {
        closeParagraph();
        closeList();
        inCode = true;
        code = [];
      }
      continue;
    }
    if (inCode) {
      code.push(line);
      continue;
    }
    if (!line.trim()) {
      closeParagraph();
      closeList();
      continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      closeParagraph();
      closeList();
      const level = heading[1].length;
      const text = heading[2].trim();
      html.push(`<h${level} id="${slugify(text)}">${inlineMarkdown(text)}</h${level}>`);
      continue;
    }
    const unordered = /^[-*]\s+(.+)$/.exec(line);
    const ordered = /^\d+\.\s+(.+)$/.exec(line);
    if (unordered || ordered) {
      closeParagraph();
      const desiredType = unordered ? 'ul' : 'ol';
      if (!inList || listType !== desiredType) {
        closeList();
        html.push(`<${desiredType}>`);
        inList = true;
        listType = desiredType;
      }
      html.push(`<li>${inlineMarkdown((unordered || ordered)[1])}</li>`);
      continue;
    }
    if (line.startsWith('> ')) {
      closeParagraph();
      closeList();
      html.push(`<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`);
      continue;
    }
    if (/^-{3,}$/.test(line.trim())) {
      closeParagraph();
      closeList();
      html.push('<hr />');
      continue;
    }
    paragraph.push(line.trim());
  }
  closeCode();
  closeParagraph();
  closeList();
  return html.join('\n');
}

function renderList(activeDoc) {
  docList.replaceChildren(...DOCS.map(([file, label]) => {
    const link = document.createElement('a');
    link.href = `#${encodeURIComponent(file)}`;
    link.textContent = label;
    if (file === activeDoc) {
      link.setAttribute('aria-current', 'page');
    }
    return link;
  }));
}

async function loadDoc() {
  const doc = currentDoc();
  const label = allowedDocs.get(doc);
  renderList(doc);
  docTitle.textContent = label;
  docMeta.textContent = `Rendering ${doc} as a styled GitHub Pages document.`;
  rawLink.href = `./${doc}`;
  githubLink.href = `https://github.com/Anstrays/arc-mcp-builder-assistant/blob/main/docs/${doc}`;
  try {
    const response = await fetch(`./${doc}`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    docBody.innerHTML = renderMarkdown(markdown);
    document.title = `${label} · Arc MCP Builder Assistant`;
  } catch (error) {
    docBody.innerHTML = `<p class="error">Could not load ${escapeHtml(doc)}. ${escapeHtml(error.message)}</p>`;
  }
}

window.addEventListener('hashchange', loadDoc);
loadDoc();

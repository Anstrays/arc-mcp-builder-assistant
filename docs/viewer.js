const PAGES = [
  { id: 'arc-mcp-setup.md', path: './arc-mcp-setup.md', githubPath: 'docs/arc-mcp-setup.md', label: 'MCP setup', group: 'Arc docs' },
  { id: 'arc-docs-map.md', path: './arc-docs-map.md', githubPath: 'docs/arc-docs-map.md', label: 'Arc docs map', group: 'Arc docs' },
  { id: 'deploy-contracts-arc.md', path: './deploy-contracts-arc.md', githubPath: 'docs/deploy-contracts-arc.md', label: 'Deploy contracts on Arc', group: 'Arc docs' },
  { id: 'builder-workflows.md', path: './builder-workflows.md', githubPath: 'docs/builder-workflows.md', label: 'Builder workflows', group: 'Builder kit' },
  { id: 'payment-intent-demo.md', path: './payment-intent-demo.md', githubPath: 'docs/payment-intent-demo.md', label: 'Payment-intent demo spec', group: 'Builder kit' },
  { id: 'payment-intent-quickstart.md', path: './payment-intent-quickstart.md', githubPath: 'docs/payment-intent-quickstart.md', label: 'Payment-intent quickstart', group: 'Builder kit' },
  { id: 'payment-status-tutorial.md', path: './payment-status-tutorial.md', githubPath: 'docs/payment-status-tutorial.md', label: 'Payment status tutorial', group: 'Builder kit' },
  { id: 'contest-demo-script.md', path: './contest-demo-script.md', githubPath: 'docs/contest-demo-script.md', label: 'Contest demo script', group: 'Builder kit' },
  { id: 'content-pack.md', path: './content-pack.md', githubPath: 'docs/content-pack.md', label: 'Blog and contest content pack', group: 'Builder kit' },
  { id: 'public-launch-packet.md', path: './public-launch-packet.md', githubPath: 'docs/public-launch-packet.md', label: 'Public launch packet', group: 'Builder kit' },
  { id: 'arc-discord-introduction.md', path: './arc-discord-introduction.md', githubPath: 'docs/arc-discord-introduction.md', label: 'Arc Discord introduction pack', group: 'Builder kit' },
  { id: 'receipt-verifier-playground.md', path: './receipt-verifier-playground.md', githubPath: 'docs/receipt-verifier-playground.md', label: 'Receipt verifier playground', group: 'Builder kit' },
  { id: 'transaction-status-playground.md', path: './transaction-status-playground.md', githubPath: 'docs/transaction-status-playground.md', label: 'Transaction status playground', group: 'Builder kit' },
  { id: 'x402-mcp-manifest.md', path: './x402-mcp-manifest.md', githubPath: 'docs/x402-mcp-manifest.md', label: 'x402 MCP manifest', group: 'Builder kit' },
  { id: 'x402-demo-transcript.md', path: './x402-demo-transcript.md', githubPath: 'docs/x402-demo-transcript.md', label: 'x402 demo transcript', group: 'Builder kit' },
  { id: 'arc-production-deployment.md', path: './arc-production-deployment.md', githubPath: 'docs/arc-production-deployment.md', label: 'Arc production deployment', group: 'Builder kit' },
  { id: 'prompt-library.md', path: './prompt-library.md', githubPath: 'docs/prompt-library.md', label: 'Prompt library', group: 'Builder kit' },
  { id: 'agent-identity-erc8004.md', path: './agent-identity-erc8004.md', githubPath: 'docs/agent-identity-erc8004.md', label: 'Agent identity notes', group: 'Builder kit' },
  { id: 'agent-identity-profile-preview.md', path: './agent-identity-profile-preview.md', githubPath: 'docs/agent-identity-profile-preview.md', label: 'Agent identity profile preview', group: 'Builder kit' },
  { id: 'arc-builder-readiness-checklist.md', path: './arc-builder-readiness-checklist.md', githubPath: 'docs/arc-builder-readiness-checklist.md', label: 'Builder readiness checklist', group: 'Playbooks' },
  { id: 'completion-contract.md', path: './completion-contract.md', githubPath: 'docs/completion-contract.md', label: 'Safe-scope completion contract', group: 'Playbooks' },
  { id: 'current-readiness-report.md', path: './current-readiness-report.md', githubPath: 'docs/current-readiness-report.md', label: 'Current readiness report', group: 'Playbooks' },
  { id: 'arc-testnet-integration-runbook.md', path: './arc-testnet-integration-runbook.md', githubPath: 'docs/arc-testnet-integration-runbook.md', label: 'Arc Testnet integration runbook', group: 'Playbooks' },
  { id: 'arc-wallet-integration-notes.md', path: './arc-wallet-integration-notes.md', githubPath: 'docs/arc-wallet-integration-notes.md', label: 'Arc wallet integration notes', group: 'Playbooks' },
  { id: 'wallet-preflight-contract.md', path: './wallet-preflight-contract.md', githubPath: 'docs/wallet-preflight-contract.md', label: 'Wallet preflight contract', group: 'Playbooks' },
  { id: 'arc-testnet-send-readiness-gate.md', path: './arc-testnet-send-readiness-gate.md', githubPath: 'docs/arc-testnet-send-readiness-gate.md', label: 'Arc Testnet send readiness gate', group: 'Playbooks' },
  { id: 'guarded-wallet-send-runbook.md', path: './guarded-wallet-send-runbook.md', githubPath: 'docs/guarded-wallet-send-runbook.md', label: 'Guarded wallet send runbook', group: 'Playbooks' },
  { id: 'custody-and-mainnet-gates.md', path: './custody-and-mainnet-gates.md', githubPath: 'docs/custody-and-mainnet-gates.md', label: 'Custody and mainnet gates', group: 'Playbooks' },
  { id: 'arc-testnet-operator-runbook.md', path: './arc-testnet-operator-runbook.md', githubPath: 'docs/arc-testnet-operator-runbook.md', label: 'Arc Testnet operator runbook', group: 'Playbooks' },
  { id: 'arc-testnet-operator-evidence.md', path: './arc-testnet-operator-evidence.md', githubPath: 'docs/arc-testnet-operator-evidence.md', label: 'Arc Testnet operator evidence packet', group: 'Playbooks' },
  { id: 'agent-commerce-use-cases.md', path: './agent-commerce-use-cases.md', githubPath: 'docs/agent-commerce-use-cases.md', label: 'Agent commerce use cases', group: 'Playbooks' },
  { id: 'agent-commerce-components.md', path: './agent-commerce-components.md', githubPath: 'docs/agent-commerce-components.md', label: 'Agent commerce components', group: 'Playbooks' },
  { id: 'agent-commerce-flow-library.md', path: './agent-commerce-flow-library.md', githubPath: 'docs/agent-commerce-flow-library.md', label: 'Agent commerce flow library', group: 'Playbooks' },
  { id: 'agent-commerce-review-packet.md', path: './agent-commerce-review-packet.md', githubPath: 'docs/agent-commerce-review-packet.md', label: 'Agent commerce review packet', group: 'Playbooks' },
  { id: 'job-escrow-demo.md', path: './job-escrow-demo.md', githubPath: 'docs/job-escrow-demo.md', label: 'Job escrow demo', group: 'Playbooks' },
  { id: 'arc-agent-treasury-lab.md', path: './arc-agent-treasury-lab.md', githubPath: 'docs/arc-agent-treasury-lab.md', label: 'Arc Agent Treasury Lab', group: 'Playbooks' },
  { id: 'mcp-query-examples.md', path: './mcp-query-examples.md', githubPath: 'docs/mcp-query-examples.md', label: 'MCP query examples', group: 'Playbooks' },
  { id: 'arc-house-submission.md', path: './arc-house-submission.md', githubPath: 'docs/arc-house-submission.md', label: 'Arc House submission draft', group: 'Playbooks' },
  { id: 'build-log.md', path: './build-log.md', githubPath: 'docs/build-log.md', label: 'Build log', group: 'Playbooks' },
  { id: 'security.md', path: '../SECURITY.md', githubPath: 'SECURITY.md', label: 'Security policy', group: 'Community' },
  { id: 'contributing.md', path: '../CONTRIBUTING.md', githubPath: 'CONTRIBUTING.md', label: 'Contributing guide', group: 'Community' },
  { id: 'code-of-conduct.md', path: '../CODE_OF_CONDUCT.md', githubPath: 'CODE_OF_CONDUCT.md', label: 'Code of conduct', group: 'Community' },
];

const pagesById = new Map(PAGES.map((page) => [page.id, page]));
const docsByFilename = new Map(PAGES.filter((page) => page.githubPath.startsWith('docs/')).map((page) => [page.githubPath.replace(/^docs\//, ''), page]));
const docTitle = document.querySelector('#doc-title');
const docMeta = document.querySelector('#doc-meta');
const docBody = document.querySelector('#doc-body');
const docList = document.querySelector('#doc-list');
const docsHomeLink = document.querySelector('#docs-home-link');
const githubLink = document.querySelector('#github-link');
const DOC_TIMEOUT_MS = 8_000;
const MAX_DOC_BYTES = 1_000_000;

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function fetchDocText(path) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), DOC_TIMEOUT_MS);
  try {
    const response = await fetch(path, { cache: 'no-store', signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    if (new TextEncoder().encode(markdown).byteLength > MAX_DOC_BYTES) {
      throw new Error('Document exceeded the 1 MB safety limit');
    }
    return markdown;
  } finally {
    window.clearTimeout(timeout);
  }
}

function currentPage() {
  let fromHash = '';
  try {
    fromHash = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim().toLowerCase();
  } catch (_error) {
    fromHash = '';
  }
  return pagesById.get(fromHash) || PAGES[0];
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[`*_()[\]#:.]/g, '')
    .replace(/[^a-z0-9а-яё]+/gi, '-')
    .replace(/^-+|-+$/g, '') || 'section';
}

function normalizeLocalDocHref(href) {
  const [path, fragment = ''] = href.split('#', 2);
  const cleanPath = path.replace(/^\.\//, '').replace(/^docs\//, '');
  const page = docsByFilename.get(cleanPath) || pagesById.get(cleanPath.toLowerCase());
  if (!page) return null;
  return `#${encodeURIComponent(page.id)}${fragment ? `-${encodeURIComponent(fragment)}` : ''}`;
}

function inlineMarkdown(line) {
  let html = escapeHtml(line);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, text, href) => {
    const safeText = escapeHtml(text);
    const cleanHref = String(href).trim();
    if (/^(https?:|mailto:|tel:)/i.test(cleanHref)) {
      return `<a href="${escapeHtml(cleanHref)}" target="_blank" rel="noopener noreferrer">${safeText}</a>`;
    }
    const localDoc = normalizeLocalDocHref(cleanHref);
    if (localDoc) {
      return `<a href="${localDoc}">${safeText}</a>`;
    }
    if (cleanHref.startsWith('#')) {
      return `<a href="${escapeHtml(cleanHref)}">${safeText}</a>`;
    }
    return `<code>${safeText}</code>`;
  });
  return html;
}

function isTableDivider(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function splitTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim());
}

function renderTable(lines, startIndex) {
  if (startIndex + 1 >= lines.length || !lines[startIndex].includes('|') || !isTableDivider(lines[startIndex + 1])) {
    return null;
  }
  const headers = splitTableRow(lines[startIndex]);
  const rows = [];
  let index = startIndex + 2;
  while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
    rows.push(splitTableRow(lines[index]));
    index += 1;
  }
  const thead = `<thead><tr>${headers.map((cell) => `<th>${inlineMarkdown(cell)}</th>`).join('')}</tr></thead>`;
  const tbody = rows.length
    ? `<tbody>${rows.map((row) => `<tr>${headers.map((_header, cellIndex) => `<td>${inlineMarkdown(row[cellIndex] || '')}</td>`).join('')}</tr>`).join('')}</tbody>`
    : '';
  return { html: `<div class="table-wrap"><table>${thead}${tbody}</table></div>`, nextIndex: index };
}

function taskPrefix(value) {
  const task = /^\[( |x|X)\]\s+(.+)$/.exec(value);
  if (!task) return inlineMarkdown(value);
  const checked = task[1].toLowerCase() === 'x';
  return `<label class="task"><input type="checkbox" disabled ${checked ? 'checked' : ''}> <span>${inlineMarkdown(task[2])}</span></label>`;
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

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].replace(/\s+$/, '');
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
    const table = renderTable(lines, i);
    if (table) {
      closeParagraph();
      closeList();
      html.push(table.html);
      i = table.nextIndex - 1;
      continue;
    }
    if (!line.trim()) {
      closeParagraph();
      closeList();
      continue;
    }
    const heading = /^(#{1,4})\s+(.+)$/.exec(line);
    if (heading) {
      closeParagraph();
      closeList();
      const level = heading[1].length;
      const text = heading[2].trim();
      html.push(`<h${level} id="${slugify(text)}">${inlineMarkdown(text)}</h${level}>`);
      continue;
    }
    const unordered = /^\s*[-*]\s+(.+)$/.exec(line);
    const ordered = /^\s*\d+\.\s+(.+)$/.exec(line);
    if (unordered || ordered) {
      closeParagraph();
      const desiredType = unordered ? 'ul' : 'ol';
      if (!inList || listType !== desiredType) {
        closeList();
        html.push(`<${desiredType}>`);
        inList = true;
        listType = desiredType;
      }
      html.push(`<li>${taskPrefix((unordered || ordered)[1])}</li>`);
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

function renderList(activePage) {
  const fragment = document.createDocumentFragment();
  let currentGroup = '';
  for (const page of PAGES) {
    if (page.group !== currentGroup) {
      currentGroup = page.group;
      const group = document.createElement('p');
      group.className = 'doc-group';
      group.textContent = currentGroup;
      fragment.append(group);
    }
    const link = document.createElement('a');
    link.href = `#${encodeURIComponent(page.id)}`;
    link.textContent = page.label;
    if (page.id === activePage.id) {
      link.setAttribute('aria-current', 'page');
    }
    fragment.append(link);
  }
  docList.replaceChildren(fragment);
}

async function loadDoc() {
  const page = currentPage();
  renderList(page);
  docTitle.textContent = page.label;
  docMeta.textContent = `Rendering ${page.githubPath} as a styled GitHub Pages document.`;
  docsHomeLink.href = '../index.html#docs';
  githubLink.href = `https://github.com/Anstrays/arc-mcp-builder-assistant/blob/main/${page.githubPath}`;
  try {
    const markdown = await fetchDocText(page.path);
    docBody.innerHTML = renderMarkdown(markdown);
    document.title = `${page.label} · Arc MCP Builder Assistant`;
  } catch (error) {
    docBody.innerHTML = `<p class="error">Could not load ${escapeHtml(page.githubPath)}. ${escapeHtml(error.message)}</p>`;
  }
}

window.addEventListener('hashchange', loadDoc);
loadDoc();

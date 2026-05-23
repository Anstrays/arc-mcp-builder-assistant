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
  { id: 'prompt-library.md', path: './prompt-library.md', githubPath: 'docs/prompt-library.md', label: 'Prompt library', group: 'Builder kit' },
  { id: 'agent-identity-erc8004.md', path: './agent-identity-erc8004.md', githubPath: 'docs/agent-identity-erc8004.md', label: 'Agent identity notes', group: 'Builder kit' },
  { id: 'arc-builder-readiness-checklist.md', path: './arc-builder-readiness-checklist.md', githubPath: 'docs/arc-builder-readiness-checklist.md', label: 'Builder readiness checklist', group: 'Playbooks' },
  { id: 'arc-testnet-integration-runbook.md', path: './arc-testnet-integration-runbook.md', githubPath: 'docs/arc-testnet-integration-runbook.md', label: 'Arc Testnet integration runbook', group: 'Playbooks' },
  { id: 'arc-wallet-integration-notes.md', path: './arc-wallet-integration-notes.md', githubPath: 'docs/arc-wallet-integration-notes.md', label: 'Arc wallet integration notes', group: 'Playbooks' },
  { id: 'agent-commerce-use-cases.md', path: './agent-commerce-use-cases.md', githubPath: 'docs/agent-commerce-use-cases.md', label: 'Agent commerce use cases', group: 'Playbooks' },
  { id: 'job-escrow-demo.md', path: './job-escrow-demo.md', githubPath: 'docs/job-escrow-demo.md', label: 'Job escrow demo', group: 'Playbooks' },
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

function currentPage() {
  const fromHash = decodeURIComponent(window.location.hash.replace(/^#/, '')).trim().toLowerCase();
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
  rawLink.href = page.path;
  githubLink.href = `https://github.com/Anstrays/arc-mcp-builder-assistant/blob/main/${page.githubPath}`;
  try {
    const response = await fetch(page.path, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    docBody.innerHTML = renderMarkdown(markdown);
    document.title = `${page.label} · Arc MCP Builder Assistant`;
  } catch (error) {
    docBody.innerHTML = `<p class="error">Could not load ${escapeHtml(page.githubPath)}. ${escapeHtml(error.message)}</p>`;
  }
}

window.addEventListener('hashchange', loadDoc);
loadDoc();

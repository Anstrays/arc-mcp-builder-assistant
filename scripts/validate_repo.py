#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    'README.md', 'SECURITY.md', 'CONTRIBUTING.md', 'LICENSE', '.gitignore',
    'docs/arc-mcp-setup.md', 'docs/arc-docs-map.md', 'docs/deploy-contracts-arc.md', 'docs/builder-workflows.md', 'docs/payment-intent-demo.md',
    'prompts/explain-arc-docs.md', 'prompts/build-payment-intent-demo.md', 'prompts/register-agent-notes.md', 'prompts/deploy-contracts-on-arc.md',
    'examples/payment-intent-demo/index.html',
    'docs/agent-commerce-kit.md',
    '.github/workflows/ci.yml',
    'arc_builder_kit/__init__.py',
    'arc_builder_kit/arc_client.py',
    'arc_builder_kit/circle_wallet_sdk.py',
    'arc_builder_kit/cli.py',
    'arc_builder_kit/mcp_server.py',
    'scripts/arc_builder_mcp_server.py',
    'tests/test_core.py',
]

secret_patterns = [
    re.compile(r'(?i)(api[_-]?key|secret|token|private[_-]?key|seed phrase)\s*=\s*[^\s<]+'),
    re.compile(r'sk-[A-Za-z0-9]{20,}'),
    re.compile(r'ghp_[A-Za-z0-9]{20,}'),
]

errors = []
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f'missing required file: {rel}')

for path in ROOT.rglob('*'):
    if path.is_dir() or '.git' in path.parts:
        continue
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
        continue
    # Skip build artifacts and compiled files
    if 'build/' in str(path.relative_to(ROOT)) or '__pycache__' in str(path):
        continue
    text = path.read_text(errors='ignore')
    for pat in secret_patterns:
        for match in pat.finditer(text):
            value = match.group(0)
            # Skip known-safe patterns (parameter names, placeholder values, test values)
            if any(placeholder in value for placeholder in ('YOUR_', '<YOUR_', 'your-', 'example', 'placeholder', 'api_key', 'entity_secret', 'test-key', 'test-secret', '="secret"')):
                continue
            # Allow single chars or dots as values (prose text, error messages)
            if len(value.split('=')[-1].strip().strip('"').strip("'")) <= 3:
                continue
            errors.append(f'possible secret pattern in {path.relative_to(ROOT)}')
            break
    if path.suffix == '.html':
        if 'javascript:' in text.lower():
            errors.append(f'unsafe javascript: URL in {path.relative_to(ROOT)}')
        # Skip inline event handler check for demo files
        if 'examples/' in str(path.relative_to(ROOT)):
            continue
        if re.search(r'\\son[a-z]+\\s*=', text, re.I):
            errors.append(f'inline event handler in {path.relative_to(ROOT)}')

if errors:
    print('VALIDATION FAILED')
    for e in errors:
        print('-', e)
    sys.exit(1)
print('VALIDATION OK')
print(f'Checked {len(required)} required files.')

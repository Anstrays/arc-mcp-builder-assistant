'use strict';

const ARC_EXPLORER_ORIGIN = 'https://testnet.arcscan.app';
const SEND_CONFIRMATION = 'SEND ARC TESTNET USDC';
const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;
const AMOUNT_RE = /^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$/;
const STATUS_CLASSES = new Set(['pending', 'estimated', 'submitted', 'confirmed', 'failed']);

let walletData = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with HTTP ${response.status}`);
  }
  return payload;
}

function showToast(message, type = '') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast show${type ? ` ${type}` : ''}`;
  window.setTimeout(() => { toast.className = 'toast'; }, 4000);
}

function shortAddress(value) {
  if (typeof value !== 'string' || value.length < 12) return value || '--';
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

function badge(status) {
  const normalized = String(status || 'unknown').toLowerCase().replaceAll('_', '-');
  const style = normalized === 'pending-user-approval' ? 'pending' : normalized;
  const node = element('span', 'badge', normalized.replaceAll('-', ' '));
  if (STATUS_CLASSES.has(style)) node.classList.add(style);
  return node;
}

function detailRow(label, value, className = '') {
  const row = element('div', 'detail-row');
  row.append(element('dt', '', label), element('dd', className, value));
  return row;
}

function parseBalances(wallet) {
  const raw = wallet.balances;
  const balances = Array.isArray(raw) ? raw : (raw?.balances || raw?.data || []);
  if (!Array.isArray(balances)) return { display: null, native: null };
  const erc20 = balances.find((entry) => entry?.token?.symbol === 'USDC' && entry?.token?.decimals === 6);
  const native = balances.find((entry) => entry?.token?.symbol === 'USDC' && entry?.token?.decimals === 18);
  return { display: erc20 || native || balances[0] || null, native };
}

async function loadWallet() {
  const balance = document.getElementById('balance-amount');
  const native = document.getElementById('balance-native');
  const status = document.getElementById('wallet-balance-status');
  try {
    const wallet = await api('/api/wallet');
    walletData = wallet;
    const parsed = parseBalances(wallet);
    if (wallet.balance_ok && parsed.display) {
      const amount = Number.parseFloat(parsed.display.amount);
      balance.textContent = Number.isFinite(amount) ? `${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })} USDC` : '--';
      native.textContent = parsed.native ? `${parsed.native.amount} USDC` : 'Not reported';
      status.textContent = 'Live Circle CLI response';
    } else {
      balance.textContent = 'Unavailable';
      native.textContent = 'Not reported';
      status.textContent = wallet.balance_error || 'Balance unavailable';
    }
    document.getElementById('wallet-addr').textContent = wallet.address || '--';
    document.getElementById('wallet-chain').textContent = wallet.chain || '--';
    const mode = document.getElementById('wallet-mode');
    mode.textContent = wallet.real_transfer_enabled ? 'Send enabled' : 'Estimate only';
    mode.className = wallet.real_transfer_enabled ? 'badge failed' : 'badge estimated';
    renderTransactions(wallet.recent_transactions, wallet.tx_ok);
  } catch (error) {
    walletData = null;
    balance.textContent = 'Backend offline';
    native.textContent = '--';
    status.textContent = error.message;
    document.getElementById('wallet-mode').textContent = 'Offline';
    renderTransactions(null, false);
  }
}

function renderTransactions(raw, ok) {
  const container = document.getElementById('tx-list');
  container.replaceChildren();
  const items = Array.isArray(raw) ? raw : (raw?.transactions || []);
  if (!ok || !Array.isArray(items) || items.length === 0) {
    container.append(element('div', 'empty', ok ? 'No transactions reported.' : 'Transaction history unavailable.'));
    return;
  }
  for (const transaction of items.slice(0, 5)) {
    const item = element('article', 'list-item');
    const top = element('div', 'list-top');
    const amount = transaction.amount || transaction.amountPaid || '--';
    top.append(element('div', 'list-title', `${amount} USDC`), badge(transaction.state || transaction.status));
    item.append(top, element('div', 'meta mono', shortAddress(transaction.txHash || transaction.transactionHash || transaction.id)));
    container.append(item);
  }
}

async function createIntent(event) {
  event.preventDefault();
  const recipient = document.getElementById('recipient').value.trim();
  const amount = document.getElementById('amount').value.trim();
  if (!ADDRESS_RE.test(recipient)) {
    showToast('Enter a valid 42-character EVM recipient address.', 'error');
    return;
  }
  if (!AMOUNT_RE.test(amount) || Number(amount) <= 0) {
    showToast('Enter a positive USDC amount with at most 6 decimals.', 'error');
    return;
  }
  try {
    const intent = await api('/api/intent', {
      method: 'POST',
      body: JSON.stringify({
        agent: document.getElementById('agent').value.trim(),
        asset: 'USDC',
        recipient,
        amount,
        memo: document.getElementById('memo').value.trim(),
      }),
    });
    showToast(`Intent ${intent.id} created.`);
    await loadIntents();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function safeExplorerHref(base, hash) {
  try {
    const url = new URL(hash, base.endsWith('/') ? base : `${base}/`);
    return url.origin === ARC_EXPLORER_ORIGIN ? url.href : '';
  } catch {
    return '';
  }
}

function intentActions(intent) {
  const actions = element('div', 'actions');
  const estimate = element('button', 'secondary', 'Estimate fee');
  estimate.type = 'button';
  estimate.dataset.intentId = intent.id;
  estimate.dataset.real = 'false';
  actions.append(estimate);
  if (walletData?.real_transfer_enabled) {
    const send = element('button', 'danger', 'Send Arc Testnet USDC');
    send.type = 'button';
    send.dataset.intentId = intent.id;
    send.dataset.real = 'true';
    actions.append(send);
  }
  return actions;
}

function renderIntent(intent) {
  const item = element('article', 'list-item');
  const top = element('div', 'list-top');
  const title = element('div');
  title.append(
    element('div', 'list-title', `${intent.amount} ${intent.asset} to ${shortAddress(intent.recipient)}`),
    element('div', 'meta', `${intent.agent || 'Payment Agent'}${intent.memo ? ` | ${intent.memo}` : ''}`),
  );
  top.append(title, badge(intent.status));
  item.append(top);
  if (intent.estimate) {
    const fee = intent.estimate.networkFeeAmount || intent.estimate.transactionFee || 'available';
    item.append(element('div', 'estimate', `Gas estimate: ${fee}`));
  }
  if (intent.status === 'pending_user_approval' || intent.status === 'estimated') {
    item.append(intentActions(intent));
  }
  if (intent.tx_hash) {
    const href = safeExplorerHref(intent.estimate?.explorerUrl || `${ARC_EXPLORER_ORIGIN}/tx/`, intent.tx_hash);
    const metadata = element('div', 'meta mono', `Transaction: ${intent.tx_hash}`);
    if (href) {
      const link = element('a', '', ' View on ArcScan');
      link.href = href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      metadata.append(link);
    }
    item.append(metadata);
  }
  return item;
}

async function loadIntents() {
  const container = document.getElementById('intent-list');
  try {
    const intents = await api('/api/intents');
    container.replaceChildren();
    if (!Array.isArray(intents) || intents.length === 0) {
      container.append(element('div', 'empty', 'No payment intents yet.'));
      return;
    }
    for (const intent of intents) container.append(renderIntent(intent));
  } catch (error) {
    container.replaceChildren(element('div', 'empty', `Intents unavailable: ${error.message}`));
  }
}

async function approveIntent(intentId, real) {
  let confirmation = '';
  if (real) {
    confirmation = window.prompt(`Type ${SEND_CONFIRMATION} to request one Arc Testnet transfer.`) || '';
    if (confirmation !== SEND_CONFIRMATION) {
      showToast('Transfer cancelled: confirmation phrase did not match.', 'error');
      return;
    }
  }
  try {
    const result = await api('/api/approve', {
      method: 'POST',
      body: JSON.stringify({ intent_id: intentId, real, confirmation }),
    });
    showToast(result.message || `Intent ${intentId}: ${result.status}`);
    await Promise.all([loadWallet(), loadIntents()]);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function loadNetworkInfo() {
  const container = document.getElementById('network-info');
  try {
    const info = await api('/api/network');
    const list = element('dl', 'detail-list');
    list.append(
      detailRow('Network', info.network),
      detailRow('Chain ID', info.chain_id),
      detailRow('RPC', info.rpc_url, 'mono'),
      detailRow('USDC token', info.usdc_token, 'mono'),
      detailRow('Wallet', info.circle_wallet, 'mono'),
    );
    container.replaceChildren(list);
  } catch (error) {
    container.replaceChildren(element('div', 'empty', `Network data unavailable: ${error.message}`));
  }
}

async function loadAll() {
  document.getElementById('refresh-all').disabled = true;
  try {
    await Promise.all([loadWallet(), loadIntents(), loadNetworkInfo()]);
  } finally {
    document.getElementById('refresh-all').disabled = false;
  }
}

document.getElementById('refresh-all').addEventListener('click', loadAll);
document.getElementById('intent-form').addEventListener('submit', createIntent);
document.getElementById('intent-list').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-intent-id]');
  if (!button) return;
  approveIntent(button.dataset.intentId, button.dataset.real === 'true');
});

loadAll();

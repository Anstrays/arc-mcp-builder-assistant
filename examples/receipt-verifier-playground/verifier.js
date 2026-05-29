const receiptInput = document.querySelector('#receipt-json');
const verifyButton = document.querySelector('#verify-receipt');
const resetButton = document.querySelector('#reset-receipt');
const verdictPill = document.querySelector('#verdict-pill');
const receiptCheckList = document.querySelector('#receipt-check-list');
const normalizedReceipt = document.querySelector('#normalized-receipt');

const ARC_RECEIPT_EXPECTATIONS = Object.freeze({
  network: 'Arc Testnet',
  expectedChainId: 5042002,
  expectedChainIdHex: '0x4cef52',
  asset: 'USDC',
  assetDecimals: 6,
  explorerUrl: 'https://testnet.arcscan.app',
  walletConnected: false,
  backendCalls: false,
  transactionBroadcast: false,
  signingEnabled: false,
  localOnly: true,
});

const RECEIPT_CHECK_IDS = Object.freeze([
  { id: 'chainId' },
  { id: 'recipient' },
  { id: 'amount' },
  { id: 'asset' },
  { id: 'intentHash' },
  { id: 'expiry' },
  { id: 'transactionHash' },
]);

const SAMPLE_RECEIPT = Object.freeze({
  network: 'arc-testnet',
  chainId: 5042002,
  recipient: '0x1111111111111111111111111111111111111111',
  amount: '5.00',
  asset: 'USDC',
  intentHash: '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  expiry: '2026-05-30T00:00:00.000Z',
  transactionHash: '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  status: 'submitted_simulated',
  safety: {
    source: 'sample local receipt',
    walletConnected: false,
    backendCalls: false,
    transactionBroadcast: false,
  },
});

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function parseReceiptJson() {
  try {
    const parsed = JSON.parse(receiptInput.value);
    if (!isPlainObject(parsed)) {
      return { ok: false, error: 'Receipt JSON must be an object.', receipt: null };
    }
    return { ok: true, error: '', receipt: parsed };
  } catch (error) {
    return { ok: false, error: `Invalid JSON: ${error.message}`, receipt: null };
  }
}

function normalizeChainId(chainId) {
  if (typeof chainId === 'number' && Number.isInteger(chainId)) return chainId;
  const value = String(chainId || '').trim().toLowerCase();
  if (/^0x[0-9a-f]+$/.test(value)) return Number.parseInt(value, 16);
  if (/^[0-9]+$/.test(value)) return Number.parseInt(value, 10);
  return Number.NaN;
}

function normalizeReceipt(rawReceipt) {
  return {
    network: String(rawReceipt.network || '').trim().toLowerCase(),
    chainId: normalizeChainId(rawReceipt.chainId),
    chainIdHex: Number.isFinite(normalizeChainId(rawReceipt.chainId))
      ? `0x${normalizeChainId(rawReceipt.chainId).toString(16)}`
      : 'invalid',
    recipient: String(rawReceipt.recipient || '').trim(),
    amount: String(rawReceipt.amount || '').trim(),
    asset: String(rawReceipt.asset || '').trim().toUpperCase(),
    intentHash: String(rawReceipt.intentHash || '').trim(),
    expiry: String(rawReceipt.expiry || '').trim(),
    transactionHash: String(rawReceipt.transactionHash || '').trim(),
    status: String(rawReceipt.status || 'unknown').trim(),
    verifier: {
      expectedNetwork: ARC_RECEIPT_EXPECTATIONS.network,
      expectedChainId: ARC_RECEIPT_EXPECTATIONS.expectedChainId,
      expectedChainIdHex: ARC_RECEIPT_EXPECTATIONS.expectedChainIdHex,
      assetDecimals: ARC_RECEIPT_EXPECTATIONS.assetDecimals,
      explorerUrl: ARC_RECEIPT_EXPECTATIONS.explorerUrl,
      walletConnected: ARC_RECEIPT_EXPECTATIONS.walletConnected,
      backendCalls: ARC_RECEIPT_EXPECTATIONS.backendCalls,
      transactionBroadcast: ARC_RECEIPT_EXPECTATIONS.transactionBroadcast,
      signingEnabled: ARC_RECEIPT_EXPECTATIONS.signingEnabled,
      localOnly: ARC_RECEIPT_EXPECTATIONS.localOnly,
    },
  };
}

function isValidAddress(value) {
  return /^0x[a-fA-F0-9]{40}$/.test(value);
}

function isValidHash(value) {
  return /^0x[a-fA-F0-9]{64}$/.test(value);
}

function isValidUsdcAmount(value) {
  return /^(?:0|[1-9]\d*)(?:\.\d{1,6})?$/.test(value) && Number(value) > 0;
}

function expiryIsFuture(value) {
  const expiryTime = new Date(value).getTime();
  return Number.isFinite(expiryTime) && expiryTime > Date.now();
}

function check(id, label, passed, detail) {
  return { id, label, passed, detail };
}

function verifyReceipt(receipt) {
  const normalized = normalizeReceipt(receipt);
  const checks = [
    check(
      'chainId',
      'Arc Testnet chain ID',
      normalized.chainId === ARC_RECEIPT_EXPECTATIONS.expectedChainId,
      `Expected ${ARC_RECEIPT_EXPECTATIONS.expectedChainId} (${ARC_RECEIPT_EXPECTATIONS.expectedChainIdHex}); got ${normalized.chainIdHex}.`
    ),
    check(
      'recipient',
      'Recipient address',
      isValidAddress(normalized.recipient),
      'Expected a 0x-prefixed 20-byte recipient address.'
    ),
    check(
      'amount',
      'USDC amount units',
      isValidUsdcAmount(normalized.amount),
      `Expected a positive ${ARC_RECEIPT_EXPECTATIONS.asset} amount with at most ${ARC_RECEIPT_EXPECTATIONS.assetDecimals} decimals.`
    ),
    check(
      'asset',
      'Receipt asset',
      normalized.asset === ARC_RECEIPT_EXPECTATIONS.asset,
      `Expected ${ARC_RECEIPT_EXPECTATIONS.asset}; got ${normalized.asset || 'missing'}.`
    ),
    check(
      'intentHash',
      'Intent hash',
      isValidHash(normalized.intentHash),
      'Expected a 32-byte 0x-prefixed intent hash.'
    ),
    check(
      'expiry',
      'Receipt expiry',
      expiryIsFuture(normalized.expiry),
      'Expected an ISO-compatible future expiry timestamp.'
    ),
    check(
      'transactionHash',
      'Transaction hash shape',
      normalized.transactionHash === '' || isValidHash(normalized.transactionHash),
      'Expected empty for local draft or a 32-byte 0x-prefixed transaction hash.'
    ),
  ];

  return {
    passed: checks.every((item) => item.passed),
    checks,
    normalized,
  };
}

function buildCheckListItem(state, message, className) {
  const listItem = document.createElement('li');
  listItem.className = className;
  const stateLabel = document.createElement('strong');
  stateLabel.textContent = state;
  listItem.append(stateLabel, ` — ${message}`);
  return listItem;
}

function renderVerification(result) {
  verdictPill.textContent = result.passed ? 'locally consistent' : 'needs review';
  verdictPill.classList.toggle('fail', !result.passed);
  receiptCheckList.replaceChildren(
    ...result.checks.map((item) => {
      const state = item.passed ? 'PASS' : 'REVIEW';
      return buildCheckListItem(state, `${item.label}: ${item.detail}`, item.passed ? 'pass' : 'fail');
    })
  );
  normalizedReceipt.textContent = JSON.stringify(result.normalized, null, 2);
}

function renderParseError(message) {
  verdictPill.textContent = 'invalid JSON';
  verdictPill.classList.add('fail');
  receiptCheckList.replaceChildren(buildCheckListItem('REVIEW', message, 'fail'));
  normalizedReceipt.textContent = JSON.stringify({ error: message, localOnly: true }, null, 2);
}

function verifyCurrentInput() {
  const parsed = parseReceiptJson();
  if (!parsed.ok) {
    renderParseError(parsed.error);
    return;
  }
  renderVerification(verifyReceipt(parsed.receipt));
}

function resetSample() {
  receiptInput.value = JSON.stringify(SAMPLE_RECEIPT, null, 2);
  verifyCurrentInput();
}

verifyButton.addEventListener('click', verifyCurrentInput);
resetButton.addEventListener('click', resetSample);
resetSample();

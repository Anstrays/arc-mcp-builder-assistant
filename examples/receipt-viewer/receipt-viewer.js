const transactionHashInput = document.querySelector('#transaction-hash');
const loadReceiptButton = document.querySelector('#load-receipt');
const resetReceiptButton = document.querySelector('#reset-receipt');
const statusPill = document.querySelector('#status-pill');
const receiptSummaryList = document.querySelector('#receipt-summary-list');
const transferLogList = document.querySelector('#transfer-log-list');
const receiptJson = document.querySelector('#receipt-json');

const ARC_RECEIPT_VIEWER = Object.freeze({
  network: 'Arc Testnet',
  expectedChainId: 5042002,
  expectedChainIdHex: '0x4cef52',
  rpcUrl: 'https://rpc.testnet.arc.network',
  explorerUrl: 'https://testnet.arcscan.app',
  usdcAddress: '0x3600000000000000000000000000000000000000',
  usdcDecimals: 6,
  walletConnected: false,
  backendCalls: false,
  readOnlyRpcCheckOnly: true,
  transactionBroadcast: false,
  signingEnabled: false,
  autonomousSpending: false,
  humanApprovalRequired: true,
});

const SAMPLE_TRANSACTION_HASH = '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const RPC_TIMEOUT_MS = 15_000;
const MAX_RPC_RESPONSE_BYTES = 1_000_000;
const RPC_REQUEST_ID = 'arc-receipt-viewer-read-only';
const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const READ_ONLY_RPC_METHODS = Object.freeze([
  { method: 'eth_chainId', params: [] },
  { method: 'eth_getTransactionReceipt', params: ['transactionHash'] },
]);

function isValidHash(value) {
  return /^0x[a-fA-F0-9]{64}$/.test(String(value || '').trim());
}

function normalizeHex(value) {
  return String(value || '').trim().toLowerCase();
}

function hashMatchesExpected(value, expectedHash) {
  return isValidHash(value) && normalizeHex(value) === normalizeHex(expectedHash);
}

function parseHexQuantity(value) {
  if (typeof value !== 'string' || !/^0x[0-9a-fA-F]+$/.test(value)) return null;
  return BigInt(value);
}

function decimalString(value) {
  return typeof value === 'bigint' ? value.toString(10) : null;
}

function formatUsdcBaseUnits(baseUnits) {
  const value = BigInt(baseUnits);
  const scale = 10n ** BigInt(ARC_RECEIPT_VIEWER.usdcDecimals);
  const whole = value / scale;
  const fraction = (value % scale).toString(10).padStart(ARC_RECEIPT_VIEWER.usdcDecimals, '0');
  const trimmed = fraction.replace(/0+$/, '');
  return trimmed ? `${whole}.${trimmed}` : whole.toString(10);
}

function topicToAddress(topic) {
  const normalized = normalizeHex(topic);
  if (!/^0x[0-9a-f]{64}$/.test(normalized)) {
    throw new Error('Transfer topic address must be a 32-byte indexed value.');
  }
  return `0x${normalized.slice(26)}`;
}

function parseTransferAmount(data) {
  const normalized = normalizeHex(data);
  if (!/^0x[0-9a-f]{64}$/.test(normalized)) {
    throw new Error('Transfer data must be a 32-byte uint256 value.');
  }
  return BigInt(normalized);
}

function decodeUsdcTransferLog(log) {
  if (!log || typeof log !== 'object' || Array.isArray(log)) return null;
  if (normalizeHex(log.address) !== ARC_RECEIPT_VIEWER.usdcAddress.toLowerCase()) return null;
  const topics = Array.isArray(log.topics) ? log.topics.map(normalizeHex) : [];
  if (topics.length < 3 || topics[0] !== TRANSFER_TOPIC) return null;
  const amountBaseUnits = parseTransferAmount(log.data);
  return {
    kind: 'arc_testnet_usdc_transfer_log',
    token: ARC_RECEIPT_VIEWER.usdcAddress,
    tokenDecimals: ARC_RECEIPT_VIEWER.usdcDecimals,
    from: topicToAddress(topics[1]),
    to: topicToAddress(topics[2]),
    amountBaseUnits: amountBaseUnits.toString(10),
    amountUsdc: formatUsdcBaseUnits(amountBaseUnits),
    logIndexHex: typeof log.logIndex === 'string' ? log.logIndex : null,
    transactionIndexHex: typeof log.transactionIndex === 'string' ? log.transactionIndex : null,
  };
}

function extractUsdcTransferLogs(receipt) {
  const logs = receipt && Array.isArray(receipt.logs) ? receipt.logs : [];
  const transfers = [];
  for (const log of logs) {
    try {
      const decoded = decodeUsdcTransferLog(log);
      if (decoded) transfers.push(decoded);
    } catch (_error) {
      transfers.push({
        kind: 'arc_testnet_usdc_transfer_log_parse_error',
        token: ARC_RECEIPT_VIEWER.usdcAddress,
        amountBaseUnits: null,
        amountUsdc: null,
        logIndexHex: log && typeof log.logIndex === 'string' ? log.logIndex : null,
      });
    }
  }
  return transfers;
}

async function rpcCall(method, params = []) {
  if (!READ_ONLY_RPC_METHODS.some((entry) => entry.method === method)) {
    throw new Error(`Blocked unreviewed RPC method: ${method}`);
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), RPC_TIMEOUT_MS);
  try {
    const response = await fetch(ARC_RECEIPT_VIEWER.rpcUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: RPC_REQUEST_ID, method, params }),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`RPC HTTP ${response.status}`);
    }
    const responseText = await response.text();
    if (new TextEncoder().encode(responseText).byteLength > MAX_RPC_RESPONSE_BYTES) {
      throw new Error('RPC response exceeded the 1 MB safety limit');
    }
    const payload = JSON.parse(responseText);
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
      throw new Error('RPC response must be a JSON object');
    }
    if (payload.jsonrpc !== '2.0' || payload.id !== RPC_REQUEST_ID) {
      throw new Error('RPC response envelope did not match the request');
    }
    const hasResult = Object.prototype.hasOwnProperty.call(payload, 'result');
    const hasError = Object.prototype.hasOwnProperty.call(payload, 'error');
    if (hasResult === hasError) {
      throw new Error('RPC response must contain exactly one result or error field');
    }
    if (hasError) {
      const message = payload.error && typeof payload.error.message === 'string'
        ? payload.error.message.slice(0, 200)
        : 'unknown RPC error';
      throw new Error(`${method} failed: ${message}`);
    }
    return payload.result;
  } catch (error) {
    if (error && error.name === 'AbortError') {
      throw new Error('Request timed out after 15 seconds.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

async function readOnlyReceiptLookup(transactionHash) {
  const chainIdHex = await rpcCall('eth_chainId');
  if (normalizeHex(chainIdHex) !== ARC_RECEIPT_VIEWER.expectedChainIdHex) {
    return { chainIdHex, receipt: null };
  }
  const receipt = await rpcCall('eth_getTransactionReceipt', [transactionHash]);
  return { chainIdHex, receipt };
}

function buildCheck(id, label, level, detail) {
  return { id, label, level, detail };
}

function safetyBoundary() {
  return {
    walletConnected: false,
    backendCalls: false,
    readOnlyRpcCheckOnly: true,
    transactionBroadcast: false,
    signingEnabled: false,
    autonomousSpending: false,
    humanApprovalRequired: true,
  };
}

function classifyReceiptStatus(chainIdHex, receipt, expectedTransactionHash) {
  const chainIdBigInt = parseHexQuantity(chainIdHex);
  const chainMatches = normalizeHex(chainIdHex) === ARC_RECEIPT_VIEWER.expectedChainIdHex;
  const receiptHashMatches = !receipt || hashMatchesExpected(receipt.transactionHash, expectedTransactionHash);
  const transferEvents = receiptHashMatches ? extractUsdcTransferLogs(receipt) : [];
  const blockNumber = receipt ? parseHexQuantity(receipt.blockNumber) : null;
  const gasUsed = receipt ? parseHexQuantity(receipt.gasUsed) : null;
  const base = {
    kind: 'arc_testnet_payment_receipt_view',
    network: ARC_RECEIPT_VIEWER.network,
    rpcUrl: ARC_RECEIPT_VIEWER.rpcUrl,
    explorerUrl: ARC_RECEIPT_VIEWER.explorerUrl,
    expectedChainId: ARC_RECEIPT_VIEWER.expectedChainId,
    expectedChainIdHex: ARC_RECEIPT_VIEWER.expectedChainIdHex,
    chainIdHex,
    chainIdDecimal: decimalString(chainIdBigInt),
    rpcChainIdMatchesArcTestnet: chainMatches,
    expectedTransactionHash,
    receiptHashMatches,
    transferEvents,
    transferEventCount: transferEvents.length,
    checkedAt: new Date().toISOString(),
    safety: safetyBoundary(),
  };

  if (!chainMatches) {
    return {
      ...base,
      state: 'unknown',
      evidenceVerdict: 'unknown_wrong_chain',
      reason: 'RPC chain ID did not match Arc Testnet.',
      receiptFound: false,
      receipt: null,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  if (!receipt) {
    return {
      ...base,
      state: 'not_found',
      evidenceVerdict: 'receipt_not_found',
      reason: 'Arc Testnet RPC returned no receipt for this hash.',
      receiptFound: false,
      receipt: null,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  if (!receiptHashMatches) {
    return {
      ...base,
      state: 'unknown',
      evidenceVerdict: 'unknown_hash_mismatch',
      reason: 'RPC returned a receipt for a different transaction hash.',
      receiptFound: true,
      observedReceiptTransactionHash: receipt.transactionHash || null,
      receipt: null,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  const common = {
    ...base,
    transactionHash: receipt.transactionHash,
    blockNumberHex: receipt.blockNumber || null,
    blockNumberDecimal: decimalString(blockNumber),
    gasUsedHex: receipt.gasUsed || null,
    gasUsedDecimal: decimalString(gasUsed),
    logsCount: Array.isArray(receipt.logs) ? receipt.logs.length : 0,
    receiptFound: true,
    receipt,
    settlementProven: false,
    businessAcceptanceProven: false,
  };

  if (receipt.status === '0x1') {
    return {
      ...common,
      state: 'success',
      evidenceVerdict: 'success_receipt_observed',
      reason: 'Transaction receipt exists and status is 0x1.',
    };
  }

  if (receipt.status === '0x0') {
    return {
      ...common,
      state: 'revert',
      evidenceVerdict: 'reverted_receipt_observed',
      reason: 'Transaction receipt exists and status is 0x0.',
    };
  }

  return {
    ...common,
    state: 'unknown',
    evidenceVerdict: 'unknown_ambiguous_receipt',
    reason: 'Receipt exists but status is missing or ambiguous.',
  };
}

function checksForResult(result, hash) {
  return [
    buildCheck(
      'hash',
      'Transaction hash shape',
      isValidHash(hash) ? 'pass' : 'fail',
      'Expected a 32-byte 0x-prefixed transaction hash.'
    ),
    buildCheck(
      'chain',
      'Arc Testnet chain ID',
      result.rpcChainIdMatchesArcTestnet ? 'pass' : 'fail',
      `Expected ${ARC_RECEIPT_VIEWER.expectedChainIdHex}; got ${result.chainIdHex || 'unavailable'}.`
    ),
    buildCheck(
      'method-scope',
      'RPC method scope',
      'pass',
      'Used only eth_chainId and eth_getTransactionReceipt.'
    ),
    buildCheck(
      'receipt-status',
      'Receipt status',
      result.state === 'success'
        ? 'pass'
        : result.state === 'revert'
          ? 'fail'
          : 'warn',
      result.reason
    ),
    buildCheck(
      'usdc-transfer-logs',
      'Pinned USDC Transfer logs',
      result.transferEventCount > 0 ? 'pass' : 'warn',
      result.transferEventCount > 0
        ? `${result.transferEventCount} Arc Testnet USDC Transfer log(s) decoded.`
        : 'No pinned Arc Testnet USDC Transfer logs were decoded.'
    ),
    buildCheck(
      'settlement-boundary',
      'Settlement boundary',
      'warn',
      'A receipt and Transfer logs do not prove business acceptance or product settlement.'
    ),
  ];
}

function renderList(target, items) {
  target.replaceChildren(
    ...items.map((item) => {
      const listItem = document.createElement('li');
      listItem.className = item.level;
      const strong = document.createElement('strong');
      strong.textContent = item.level === 'pass' ? 'PASS' : item.level === 'fail' ? 'REVIEW' : 'INFO';
      listItem.append(strong, ` - ${item.label}: ${item.detail}`);
      return listItem;
    })
  );
}

function renderTransferLogs(transfers) {
  if (!transfers.length) {
    renderList(transferLogList, [
      buildCheck(
        'no-usdc-transfer-logs',
        'USDC logs',
        'warn',
        'No Arc Testnet USDC Transfer logs were found in this receipt.'
      ),
    ]);
    return;
  }
  renderList(transferLogList, transfers.map((transfer, index) => buildCheck(
    `usdc-transfer-${index + 1}`,
    `${transfer.from || 'unknown'} -> ${transfer.to || 'unknown'}`,
    transfer.amountBaseUnits ? 'pass' : 'warn',
    transfer.amountBaseUnits
      ? `${transfer.amountUsdc} USDC (${transfer.amountBaseUnits} base units).`
      : 'Transfer log matched the pinned token/topic but could not be fully decoded.'
  )));
}

function renderStatus(result) {
  statusPill.textContent = result.state;
  statusPill.className = `status ${result.state}`;
  renderList(receiptSummaryList, checksForResult(result, result.expectedTransactionHash || transactionHashInput.value.trim()));
  renderTransferLogs(result.transferEvents || []);
  receiptJson.textContent = JSON.stringify(result, null, 2);
}

function renderInitialState() {
  const result = {
    kind: 'arc_testnet_payment_receipt_view',
    state: 'not_checked',
    evidenceVerdict: 'not_checked',
    reason: 'No read-only receipt lookup has run yet.',
    network: ARC_RECEIPT_VIEWER.network,
    rpcUrl: ARC_RECEIPT_VIEWER.rpcUrl,
    expectedChainId: ARC_RECEIPT_VIEWER.expectedChainId,
    expectedChainIdHex: ARC_RECEIPT_VIEWER.expectedChainIdHex,
    transferEvents: [],
    transferEventCount: 0,
    settlementProven: false,
    businessAcceptanceProven: false,
    safety: safetyBoundary(),
  };
  renderStatus(result);
}

function renderValidationError(hash, reason = 'Transaction hash is not a 32-byte 0x-prefixed value.') {
  const result = {
    kind: 'arc_testnet_payment_receipt_view',
    state: 'unknown',
    evidenceVerdict: 'invalid_local_input',
    reason,
    checkedAt: new Date().toISOString(),
    expectedTransactionHash: hash,
    chainIdHex: 'not_checked',
    rpcChainIdMatchesArcTestnet: false,
    transferEvents: [],
    transferEventCount: 0,
    settlementProven: false,
    businessAcceptanceProven: false,
    safety: safetyBoundary(),
  };
  renderStatus(result);
}

async function loadReceipt() {
  const hash = transactionHashInput.value.trim();
  if (!isValidHash(hash)) {
    renderValidationError(hash);
    return;
  }
  statusPill.textContent = 'checking';
  statusPill.className = 'status checking';
  loadReceiptButton.disabled = true;
  receiptJson.textContent = JSON.stringify({ state: 'checking_arc_receipt', transactionHash: hash }, null, 2);
  try {
    const lookup = await readOnlyReceiptLookup(hash);
    const result = classifyReceiptStatus(lookup.chainIdHex, lookup.receipt, hash);
    renderStatus(result);
  } catch (error) {
    const result = {
      kind: 'arc_testnet_payment_receipt_view',
      state: 'unknown',
      evidenceVerdict: 'unknown_rpc_unavailable',
      reason: `RPC receipt lookup unavailable: ${error.message}`,
      checkedAt: new Date().toISOString(),
      expectedTransactionHash: hash,
      chainIdHex: 'unavailable',
      rpcUrl: ARC_RECEIPT_VIEWER.rpcUrl,
      rpcChainIdMatchesArcTestnet: false,
      transferEvents: [],
      transferEventCount: 0,
      settlementProven: false,
      businessAcceptanceProven: false,
      safety: safetyBoundary(),
    };
    renderStatus(result);
  } finally {
    loadReceiptButton.disabled = false;
  }
}

function resetSample() {
  transactionHashInput.value = SAMPLE_TRANSACTION_HASH;
  renderInitialState();
}

loadReceiptButton.addEventListener('click', loadReceipt);
resetReceiptButton.addEventListener('click', resetSample);
renderInitialState();

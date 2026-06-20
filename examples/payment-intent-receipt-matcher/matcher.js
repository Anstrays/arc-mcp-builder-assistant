const transactionHashInput = document.querySelector('#transaction-hash');
const intentInput = document.querySelector('#payment-intent');
const matchButton = document.querySelector('#match-receipt');
const resetButton = document.querySelector('#reset-matcher');
const statusPill = document.querySelector('#status-pill');
const matchSummaryList = document.querySelector('#match-summary-list');
const transferLogList = document.querySelector('#transfer-log-list');
const matchJson = document.querySelector('#match-json');

const ARC_MATCHER = Object.freeze({
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

const SAMPLE_INTENT = JSON.stringify({
  version: '2025-06-arc-payment-intent-v1',
  network: 'Arc Testnet',
  chainId: 5042002,
  asset: 'USDC',
  token: '0x3600000000000000000000000000000000000000',
  recipient: '0x1111111111111111111111111111111111111111',
  amount: '0.01',
  amountBaseUnits: '10000',
  decimals: 6,
  memo: 'Demo payment-intent receipt matcher',
}, null, 2);

const SAMPLE_TRANSACTION_HASH = '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const RPC_TIMEOUT_MS = 15_000;
const MAX_RPC_RESPONSE_BYTES = 1_000_000;
const RPC_REQUEST_ID = 'arc-payment-intent-receipt-matcher-read-only';
const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const MAX_INTENT_INPUT_LENGTH = 16_384;
const MAX_UINT256_DECIMAL_DIGITS = 78;
const MAX_DECIMAL_INPUT_LENGTH = 96;
const READ_ONLY_RPC_METHODS = Object.freeze([
  { method: 'eth_chainId', params: [] },
  { method: 'eth_getTransactionReceipt', params: ['transactionHash'] },
]);

const ZERO_ADDRESS = '0x' + '0'.repeat(40);

function isValidHash(value) {
  return /^0x[a-fA-F0-9]{64}$/.test(String(value || '').trim());
}

function normalizeHex(value) {
  return String(value || '').trim().toLowerCase();
}

function isValidEvmAddress(value) {
  return /^0x[0-9a-fA-F]{40}$/.test(String(value || '').trim());
}

function isNonZeroAddress(value) {
  return isValidEvmAddress(value) && normalizeHex(value) !== ZERO_ADDRESS;
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
  const scale = 10n ** BigInt(ARC_MATCHER.usdcDecimals);
  const whole = value / scale;
  const fraction = (value % scale).toString(10).padStart(ARC_MATCHER.usdcDecimals, '0');
  const trimmed = fraction.replace(/0+$/, '');
  return trimmed ? `${whole}.${trimmed}` : whole.toString(10);
}

function parseAmountBaseUnits(value) {
  const trimmed = String(value || '').trim();
  if (!trimmed) return null;
  if (trimmed.length > MAX_UINT256_DECIMAL_DIGITS) return null;
  // Reject hex, signs, scientific notation, commas, decimals, and leading zeros.
  if (!/^[1-9]\d*$/.test(trimmed)) return null;
  try {
    return BigInt(trimmed);
  } catch (_error) {
    return null;
  }
}

function usdcBaseUnitsFromDecimal(decimalStringValue) {
  const trimmed = String(decimalStringValue || '').trim();
  if (!trimmed) return null;
  if (trimmed.length > MAX_DECIMAL_INPUT_LENGTH) return null;

  // Allow "1" or "0.01", but reject signs, scientific notation, commas, hex, empty parts,
  // leading zeros, and anything with more than usdcDecimals fractional digits.
  const isInteger = /^[1-9]\d*$/.test(trimmed);
  const isDecimal = /^(0|[1-9]\d*)\.\d+$/.test(trimmed);
  if (!isInteger && !isDecimal) return null;

  const [wholePart, fractionPart = ''] = trimmed.split('.');
  if (wholePart.length > MAX_UINT256_DECIMAL_DIGITS) return null;
  if (fractionPart.length > ARC_MATCHER.usdcDecimals) return null;

  const scale = 10n ** BigInt(ARC_MATCHER.usdcDecimals);
  const whole = BigInt(wholePart || '0');
  const fractionPadded = fractionPart.padEnd(ARC_MATCHER.usdcDecimals, '0');
  const fraction = BigInt(fractionPadded);
  const baseUnits = whole * scale + fraction;

  // Reject zero and negative (the regex already rejects '-' signs; this is a second guard).
  if (baseUnits <= 0n) return null;
  return baseUnits;
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
  if (normalizeHex(log.address) !== ARC_MATCHER.usdcAddress.toLowerCase()) return null;
  const topics = Array.isArray(log.topics) ? log.topics.map(normalizeHex) : [];
  if (topics.length < 3 || topics[0] !== TRANSFER_TOPIC) return null;
  const amountBaseUnits = parseTransferAmount(log.data);
  return {
    kind: 'arc_testnet_usdc_transfer_log',
    token: ARC_MATCHER.usdcAddress,
    tokenDecimals: ARC_MATCHER.usdcDecimals,
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
        token: ARC_MATCHER.usdcAddress,
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
    const response = await fetch(ARC_MATCHER.rpcUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: RPC_REQUEST_ID, method, params }),
      signal: controller.signal,
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
      cache: 'no-store',
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
  if (normalizeHex(chainIdHex) !== ARC_MATCHER.expectedChainIdHex) {
    return { chainIdHex, receipt: null };
  }
  const receipt = await rpcCall('eth_getTransactionReceipt', [transactionHash]);
  return { chainIdHex, receipt };
}

function parseIntent(rawValue) {
  const text = String(rawValue || '').trim();
  if (!text) {
    return { ok: false, error: 'Payment intent is empty.', intent: null };
  }
  if (text.length > MAX_INTENT_INPUT_LENGTH) {
    return { ok: false, error: 'Payment intent input is too large.', intent: null };
  }
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    return { ok: false, error: `Payment intent is not valid JSON: ${error.message}`, intent: null };
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return { ok: false, error: 'Payment intent must be a JSON object.', intent: null };
  }

  // Network pinning: only Arc Testnet is supported.
  const network = parsed.network;
  if (network !== 'Arc Testnet' && network !== 'arc-testnet') {
    return { ok: false, error: "Payment intent network must be 'Arc Testnet' or 'arc-testnet'.", intent: null };
  }
  if (parsed.chainId !== ARC_MATCHER.expectedChainId) {
    return { ok: false, error: `Payment intent chainId must be ${ARC_MATCHER.expectedChainId}.`, intent: null };
  }
  if (parsed.asset !== 'USDC') {
    return { ok: false, error: "Payment intent asset must be 'USDC'.", intent: null };
  }

  // Token pinning: reject any token other than the canonical Arc Testnet USDC contract.
  const token = normalizeHex(parsed.token);
  if (token !== ARC_MATCHER.usdcAddress.toLowerCase()) {
    return { ok: false, error: 'Payment intent token must be the pinned Arc Testnet USDC contract.', intent: null };
  }

  // Decimals pinning: only 6 decimals are supported for Arc Testnet USDC.
  if (parsed.decimals !== ARC_MATCHER.usdcDecimals) {
    return { ok: false, error: `Payment intent decimals must be ${ARC_MATCHER.usdcDecimals}.`, intent: null };
  }

  // Recipient must be a non-zero 20-byte EVM address and must not be the token contract.
  const recipient = normalizeHex(parsed.recipient);
  if (!isNonZeroAddress(recipient)) {
    return { ok: false, error: 'Payment intent recipient must include a valid non-zero 20-byte recipient address.', intent: null };
  }
  if (recipient === ARC_MATCHER.usdcAddress.toLowerCase()) {
    return { ok: false, error: 'Payment intent recipient must not be the USDC token contract.', intent: null };
  }

  // Amount: at least one of amount or amountBaseUnits must be present.
  const hasAmount = typeof parsed.amount === 'string' && parsed.amount.trim() !== '';
  const hasBaseUnits = typeof parsed.amountBaseUnits === 'string' && parsed.amountBaseUnits.trim() !== '';
  if (!hasAmount && !hasBaseUnits) {
    return { ok: false, error: 'Payment intent must include amount or amountBaseUnits.', intent: null };
  }

  let amountBaseUnits = null;
  if (hasBaseUnits) {
    amountBaseUnits = parseAmountBaseUnits(parsed.amountBaseUnits);
    if (amountBaseUnits === null) {
      return { ok: false, error: 'Payment intent amountBaseUnits must be a positive base-10 integer string.', intent: null };
    }
  }
  if (hasAmount) {
    const decimalBaseUnits = usdcBaseUnitsFromDecimal(parsed.amount);
    if (decimalBaseUnits === null) {
      return { ok: false, error: 'Payment intent amount must be a positive decimal with at most 6 fractional digits.', intent: null };
    }
    if (hasBaseUnits && decimalBaseUnits !== amountBaseUnits) {
      return { ok: false, error: 'Payment intent amount and amountBaseUnits do not match.', intent: null };
    }
    amountBaseUnits = decimalBaseUnits;
  }

  const intent = {
    version: typeof parsed.version === 'string' ? parsed.version : null,
    network,
    chainId: parsed.chainId,
    asset: parsed.asset,
    token,
    recipient,
    amountBaseUnits,
    decimals: parsed.decimals,
    memo: typeof parsed.memo === 'string' ? parsed.memo : null,
  };
  return { ok: true, error: null, intent };
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

function classifyMatch({ chainIdHex, receipt }, transactionHash, intent) {
  const chainIdBigInt = parseHexQuantity(chainIdHex);
  const chainMatches = normalizeHex(chainIdHex) === ARC_MATCHER.expectedChainIdHex;
  const receiptHashMatches = !receipt || hashMatchesExpected(receipt.transactionHash, transactionHash);
  const transferEvents = receiptHashMatches ? extractUsdcTransferLogs(receipt) : [];
  const matchingTransfers = transferEvents.filter((transfer) => {
    if (!transfer.amountBaseUnits) return false;
    const transferAmount = BigInt(transfer.amountBaseUnits);
    return transfer.to === intent.recipient
      && transfer.token.toLowerCase() === intent.token
      && transferAmount === intent.amountBaseUnits;
  });
  const base = {
    kind: 'arc_testnet_payment_intent_receipt_match',
    network: ARC_MATCHER.network,
    rpcUrl: ARC_MATCHER.rpcUrl,
    explorerUrl: ARC_MATCHER.explorerUrl,
    expectedChainId: ARC_MATCHER.expectedChainId,
    expectedChainIdHex: ARC_MATCHER.expectedChainIdHex,
    chainIdHex,
    chainIdDecimal: decimalString(chainIdBigInt),
    rpcChainIdMatchesArcTestnet: chainMatches,
    expectedTransactionHash: transactionHash,
    receiptHashMatches,
    intent: {
      ...intent,
      amountBaseUnits: intent.amountBaseUnits.toString(10),
      amountUsdc: formatUsdcBaseUnits(intent.amountBaseUnits),
    },
    transferEvents,
    transferEventCount: transferEvents.length,
    matchingTransferCount: matchingTransfers.length,
    matchingTransfers,
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
      intentMatched: false,
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
      intentMatched: false,
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
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  const common = {
    ...base,
    transactionHash: receipt.transactionHash,
    blockNumberHex: receipt.blockNumber || null,
    blockNumberDecimal: decimalString(parseHexQuantity(receipt.blockNumber)),
    gasUsedHex: receipt.gasUsed || null,
    gasUsedDecimal: decimalString(parseHexQuantity(receipt.gasUsed)),
    logsCount: Array.isArray(receipt.logs) ? receipt.logs.length : 0,
    receiptFound: true,
    receipt,
  };

  if (receipt.status !== '0x1') {
    return {
      ...common,
      state: 'revert',
      evidenceVerdict: 'reverted_receipt_observed',
      reason: 'Transaction receipt exists but status is not 0x1, so no successful transfer is expected.',
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  if (matchingTransfers.length === 0) {
    return {
      ...common,
      state: 'mismatch',
      evidenceVerdict: 'intent_receipt_mismatch',
      reason: 'Receipt succeeded, but no USDC Transfer log matched the expected recipient, token, and amount.',
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
    };
  }

  return {
    ...common,
    state: 'match',
    evidenceVerdict: 'intent_receipt_match_observed',
    reason: 'Receipt succeeded and at least one USDC Transfer log matched the expected recipient, token, and amount.',
    intentMatched: true,
    settlementProven: false,
    businessAcceptanceProven: false,
  };
}

function buildCheck(id, label, level, detail) {
  return { id, label, level, detail };
}

function checksForResult(result, hash, intent) {
  const checks = [
    buildCheck(
      'hash',
      'Transaction hash shape',
      isValidHash(hash) ? 'pass' : 'fail',
      'Expected a 32-byte 0x-prefixed transaction hash.'
    ),
    buildCheck(
      'intent',
      'Payment intent parse',
      intent && !intent.error ? 'pass' : 'fail',
      intent && !intent.error ? 'Intent parsed successfully.' : (intent && intent.error) || 'Intent is missing or invalid.'
    ),
    buildCheck(
      'chain',
      'Arc Testnet chain ID',
      result.rpcChainIdMatchesArcTestnet ? 'pass' : 'fail',
      `Expected ${ARC_MATCHER.expectedChainIdHex}; got ${result.chainIdHex || 'unavailable'}.`
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
      result.state === 'match'
        ? 'pass'
        : result.state === 'revert' || result.state === 'mismatch'
          ? 'fail'
          : 'warn',
      result.reason
    ),
    buildCheck(
      'usdc-transfer-match',
      'USDC Transfer matches intent',
      result.matchingTransferCount > 0 ? 'pass' : 'warn',
      result.matchingTransferCount > 0
        ? `${result.matchingTransferCount} Arc Testnet USDC Transfer log(s) matched the intent.`
        : 'No pinned Arc Testnet USDC Transfer log matched the intent.'
    ),
    buildCheck(
      'settlement-boundary',
      'Settlement boundary',
      'warn',
      'A chain-side match does not prove business acceptance, offchain fulfillment, or product settlement.'
    ),
  ];
  return checks;
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

function renderTransferLogs(transfers, intent) {
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
  renderList(transferLogList, transfers.map((transfer, index) => {
    const matchesIntent = transfer.amountBaseUnits
      && transfer.to === intent.recipient
      && transfer.token.toLowerCase() === intent.token
      && BigInt(transfer.amountBaseUnits) === intent.amountBaseUnits;
    return buildCheck(
      `usdc-transfer-${index + 1}`,
      `${transfer.from || 'unknown'} -> ${transfer.to || 'unknown'}`,
      transfer.amountBaseUnits ? (matchesIntent ? 'pass' : 'warn') : 'warn',
      transfer.amountBaseUnits
        ? `${transfer.amountUsdc} USDC (${transfer.amountBaseUnits} base units)${matchesIntent ? ' ✓ matches intent' : ' ✗ does not match intent'}.`
        : 'Transfer log matched the pinned token/topic but could not be fully decoded.'
    );
  }));
}

function renderStatus(result, hash, intent) {
  statusPill.textContent = result.state;
  statusPill.className = `status ${result.state}`;
  renderList(matchSummaryList, checksForResult(result, hash, intent));
  renderTransferLogs(result.transferEvents || [], intent);
  matchJson.textContent = JSON.stringify(result, null, 2);
}

function renderInitialState() {
  const result = {
    kind: 'arc_testnet_payment_intent_receipt_match',
    state: 'not_checked',
    evidenceVerdict: 'not_checked',
    reason: 'No payment-intent receipt match has run yet.',
    network: ARC_MATCHER.network,
    rpcUrl: ARC_MATCHER.rpcUrl,
    expectedChainId: ARC_MATCHER.expectedChainId,
    expectedChainIdHex: ARC_MATCHER.expectedChainIdHex,
    transferEvents: [],
    transferEventCount: 0,
    matchingTransferCount: 0,
    intentMatched: false,
    settlementProven: false,
    businessAcceptanceProven: false,
    safety: safetyBoundary(),
  };
  renderStatus(result, '', { error: 'Intent not parsed.' });
}

async function runMatch() {
  const hash = transactionHashInput.value.trim();
  const intentParse = parseIntent(intentInput.value);
  if (!isValidHash(hash)) {
    const result = {
      kind: 'arc_testnet_payment_intent_receipt_match',
      state: 'unknown',
      evidenceVerdict: 'invalid_local_input',
      reason: 'Transaction hash is not a 32-byte 0x-prefixed value.',
      checkedAt: new Date().toISOString(),
      expectedTransactionHash: hash,
      intent: intentParse.ok ? { ...intentParse.intent, amountBaseUnits: intentParse.intent.amountBaseUnits.toString(10) } : null,
      chainIdHex: 'not_checked',
      rpcChainIdMatchesArcTestnet: false,
      transferEvents: [],
      transferEventCount: 0,
      matchingTransferCount: 0,
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
      safety: safetyBoundary(),
    };
    renderStatus(result, hash, intentParse);
    return;
  }
  if (!intentParse.ok) {
    const result = {
      kind: 'arc_testnet_payment_intent_receipt_match',
      state: 'unknown',
      evidenceVerdict: 'invalid_local_input',
      reason: intentParse.error,
      checkedAt: new Date().toISOString(),
      expectedTransactionHash: hash,
      intent: null,
      chainIdHex: 'not_checked',
      rpcChainIdMatchesArcTestnet: false,
      transferEvents: [],
      transferEventCount: 0,
      matchingTransferCount: 0,
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
      safety: safetyBoundary(),
    };
    renderStatus(result, hash, intentParse);
    return;
  }
  statusPill.textContent = 'checking';
  statusPill.className = 'status checking';
  matchButton.disabled = true;
  matchJson.textContent = JSON.stringify({ state: 'checking_arc_receipt_match', transactionHash: hash }, null, 2);
  try {
    const lookup = await readOnlyReceiptLookup(hash);
    const result = classifyMatch(lookup, hash, intentParse.intent);
    renderStatus(result, hash, intentParse.intent);
  } catch (error) {
    const result = {
      kind: 'arc_testnet_payment_intent_receipt_match',
      state: 'unknown',
      evidenceVerdict: 'unknown_rpc_unavailable',
      reason: `RPC receipt lookup unavailable: ${error.message}`,
      checkedAt: new Date().toISOString(),
      expectedTransactionHash: hash,
      intent: { ...intentParse.intent, amountBaseUnits: intentParse.intent.amountBaseUnits.toString(10) },
      chainIdHex: 'unavailable',
      rpcUrl: ARC_MATCHER.rpcUrl,
      rpcChainIdMatchesArcTestnet: false,
      transferEvents: [],
      transferEventCount: 0,
      matchingTransferCount: 0,
      intentMatched: false,
      settlementProven: false,
      businessAcceptanceProven: false,
      safety: safetyBoundary(),
    };
    renderStatus(result, hash, intentParse.intent);
  } finally {
    matchButton.disabled = false;
  }
}

function resetSample() {
  transactionHashInput.value = SAMPLE_TRANSACTION_HASH;
  intentInput.value = SAMPLE_INTENT;
  renderInitialState();
}

matchButton.addEventListener('click', runMatch);
resetButton.addEventListener('click', resetSample);
renderInitialState();

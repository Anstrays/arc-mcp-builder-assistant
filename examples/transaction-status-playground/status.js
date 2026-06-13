const transactionHashInput = document.querySelector('#transaction-hash');
const expectedRecipientInput = document.querySelector('#expected-recipient');
const expectedAmountInput = document.querySelector('#expected-amount');
const checkButton = document.querySelector('#check-transaction');
const resetButton = document.querySelector('#reset-transaction');
const statusPill = document.querySelector('#status-pill');
const statusCheckList = document.querySelector('#status-check-list');
const transactionStatusJson = document.querySelector('#transaction-status-json');

const ARC_TRANSACTION_STATUS = Object.freeze({
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
  autonomousSpending: false,
  humanApprovalRequired: true,
  signingRequiresWalletChainGateAndHumanApproval: true,
});

const SAMPLE_TRANSACTION_HASH = '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const RPC_TIMEOUT_MS = 10_000;
const MAX_RPC_RESPONSE_BYTES = 1_000_000;
const RPC_REQUEST_ID = 'arc-transaction-status-read-only';
const TRANSFER_SELECTOR = 'a9059cbb';
const READ_ONLY_RPC_METHODS = Object.freeze([
  { method: 'eth_chainId', params: [] },
  { method: 'eth_getTransactionByHash', params: ['transactionHash'] },
  { method: 'eth_getTransactionReceipt', params: ['transactionHash'] },
]);

function isValidHash(value) {
  return /^0x[a-fA-F0-9]{64}$/.test(String(value || '').trim());
}

function hashMatchesExpected(value, expectedHash) {
  return isValidHash(value) && String(value).toLowerCase() === expectedHash.toLowerCase();
}

function parseHexQuantity(value) {
  if (typeof value !== 'string' || !/^0x[0-9a-fA-F]+$/.test(value)) return null;
  return Number.parseInt(value, 16);
}

function isNonZeroAddress(value) {
  return /^0x[a-fA-F0-9]{40}$/.test(String(value || '').trim())
    && !/^0x0{40}$/i.test(String(value || '').trim());
}

function parseUsdcAmount(rawValue) {
  const value = String(rawValue || '').trim();
  if (!/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$/.test(value)) {
    throw new Error('Expected USDC amount must be a plain positive decimal with at most 6 fractional digits.');
  }
  const [whole, fraction = ''] = value.split('.');
  const baseUnits = (BigInt(whole) * 1000000n) + BigInt(fraction.padEnd(6, '0'));
  if (baseUnits <= 0n) throw new Error('Expected USDC amount must be greater than zero.');
  return { decimal: value, baseUnits: baseUnits.toString() };
}

function decodeTransferCalldata(data) {
  const normalized = String(data || '').toLowerCase();
  if (!new RegExp(`^0x${TRANSFER_SELECTOR}[0-9a-f]{128}$`).test(normalized)) {
    throw new Error('Transaction input is not ERC-20 transfer(address,uint256) calldata.');
  }
  return {
    method: 'transfer(address,uint256)',
    recipient: `0x${normalized.slice(34, 74)}`,
    amountBaseUnits: BigInt(`0x${normalized.slice(74, 138)}`).toString(),
  };
}

function buildExpectedTransfer() {
  const recipient = expectedRecipientInput.value.trim().toLowerCase();
  if (!isNonZeroAddress(recipient)) {
    throw new Error('Expected recipient must be a non-zero 0x-prefixed 20-byte address.');
  }
  if (recipient === ARC_TRANSACTION_STATUS.usdcAddress.toLowerCase()) {
    throw new Error('Expected recipient cannot be the pinned USDC token contract.');
  }
  const amount = parseUsdcAmount(expectedAmountInput.value);
  return {
    token: ARC_TRANSACTION_STATUS.usdcAddress,
    tokenDecimals: ARC_TRANSACTION_STATUS.usdcDecimals,
    recipient,
    amountDecimal: amount.decimal,
    amountBaseUnits: amount.baseUnits,
  };
}

function reviewExpectedTransfer(transaction, expectedTransfer) {
  if (!transaction || typeof transaction !== 'object' || Array.isArray(transaction)) {
    return {
      state: 'unknown',
      allMatched: false,
      reason: 'Transaction was not found, so expected transfer fields cannot be compared.',
      checks: [],
      observed: null,
    };
  }
  let decoded = null;
  let decodeError = '';
  try {
    decoded = decodeTransferCalldata(transaction.input);
  } catch (error) {
    decodeError = error.message;
  }
  const checks = [
    {
      id: 'token-target',
      passed: String(transaction.to || '').toLowerCase() === expectedTransfer.token.toLowerCase(),
      detail: 'Transaction target must be the pinned Arc Testnet USDC interface.',
    },
    {
      id: 'zero-native-value',
      passed: parseHexQuantity(transaction.value) === 0,
      detail: 'ERC-20 transfer must send zero native value.',
    },
    {
      id: 'transfer-calldata',
      passed: Boolean(decoded),
      detail: decoded ? 'Calldata decodes as transfer(address,uint256).' : decodeError,
    },
    {
      id: 'recipient',
      passed: Boolean(decoded && decoded.recipient === expectedTransfer.recipient),
      detail: 'Decoded recipient must match the expected recipient.',
    },
    {
      id: 'amount',
      passed: Boolean(decoded && decoded.amountBaseUnits === expectedTransfer.amountBaseUnits),
      detail: 'Decoded 6-decimal USDC base units must match the expected amount.',
    },
  ];
  const allMatched = checks.every((check) => check.passed);
  return {
    state: allMatched ? 'match' : 'mismatch',
    allMatched,
    reason: allMatched
      ? 'Observed transaction shape matches the expected Arc Testnet USDC transfer.'
      : 'Observed transaction shape does not match every expected transfer field.',
    checks,
    observed: {
      from: transaction.from || null,
      tokenTarget: transaction.to || null,
      nativeValue: transaction.value || null,
      decoded,
    },
  };
}

function withTransferEvidence(result, transaction, expectedTransfer) {
  const transferReview = reviewExpectedTransfer(transaction, expectedTransfer);
  const evidenceVerdict = !result.rpcChainIdMatchesArcTestnet
    ? 'unknown_wrong_chain'
    : result.rpcObjectHashesMatch === false
      ? 'unknown_hash_mismatch'
    : transferReview.state === 'mismatch'
      ? 'mismatch_expected_transfer'
      : transferReview.state === 'unknown'
        ? 'unknown_expected_transfer'
        : `${result.state}_expected_transfer_shape`;
  return {
    ...result,
    expectedTransfer,
    transferReview,
    evidenceVerdict,
    settlementProven: false,
    businessAcceptanceProven: false,
  };
}

async function rpcCall(method, params = []) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), RPC_TIMEOUT_MS);
  try {
    const response = await fetch(ARC_TRANSACTION_STATUS.rpcUrl, {
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
  } finally {
    window.clearTimeout(timeout);
  }
}

async function readOnlyLookup(transactionHash) {
  const chainIdHex = await rpcCall('eth_chainId');
  if (parseHexQuantity(chainIdHex) !== ARC_TRANSACTION_STATUS.expectedChainId) {
    return { chainIdHex, transaction: null, receipt: null };
  }
  const transaction = await rpcCall('eth_getTransactionByHash', [transactionHash]);
  const receipt = await rpcCall('eth_getTransactionReceipt', [transactionHash]);
  return { chainIdHex, transaction, receipt };
}

function buildCheck(id, label, level, detail) {
  return { id, label, level, detail };
}

function classifyTransactionStatus(chainIdHex, transaction, receipt, expectedTransfer, expectedTransactionHash) {
  const chainIdDecimal = parseHexQuantity(chainIdHex);
  const chainMatches = chainIdDecimal === ARC_TRANSACTION_STATUS.expectedChainId;
  const transactionHashMatches = !transaction || hashMatchesExpected(transaction.hash, expectedTransactionHash);
  const receiptHashMatches = !receipt || hashMatchesExpected(receipt.transactionHash, expectedTransactionHash);
  const rpcObjectHashesMatch = transactionHashMatches && receiptHashMatches;
  const base = {
    kind: 'arc_testnet_transaction_status',
    network: ARC_TRANSACTION_STATUS.network,
    rpcUrl: ARC_TRANSACTION_STATUS.rpcUrl,
    explorerUrl: ARC_TRANSACTION_STATUS.explorerUrl,
    expectedChainId: ARC_TRANSACTION_STATUS.expectedChainId,
    expectedChainIdHex: ARC_TRANSACTION_STATUS.expectedChainIdHex,
    chainIdHex,
    chainIdDecimal,
    rpcChainIdMatchesArcTestnet: chainMatches,
    expectedTransactionHash,
    transactionHashMatches,
    receiptHashMatches,
    rpcObjectHashesMatch,
    checkedAt: new Date().toISOString(),
    safety: {
      walletConnected: false,
      backendCalls: false,
      readOnlyRpcCheckOnly: true,
      transactionBroadcast: false,
      autonomousSpending: false,
      humanApprovalRequired: true,
      signingRequiresWalletChainGateAndHumanApproval: true,
    },
  };

  if (!chainMatches) {
    return withTransferEvidence({
      ...base,
      state: 'unknown',
      reason: 'RPC chain ID did not match Arc Testnet.',
      transactionFound: Boolean(transaction),
      receiptFound: Boolean(receipt),
      transaction,
      receipt,
    }, transaction, expectedTransfer);
  }

  if (!rpcObjectHashesMatch) {
    return withTransferEvidence({
      ...base,
      state: 'unknown',
      reason: 'RPC returned a transaction or receipt for a different hash.',
      transactionFound: Boolean(transaction),
      receiptFound: Boolean(receipt),
      observedTransactionHash: transaction && transaction.hash ? transaction.hash : null,
      observedReceiptTransactionHash: receipt && receipt.transactionHash ? receipt.transactionHash : null,
    }, null, expectedTransfer);
  }

  if (receipt && receipt.status === '0x1') {
    return withTransferEvidence({
      ...base,
      state: 'confirmed',
      reason: 'Transaction receipt exists and status is 0x1.',
      transactionHash: receipt.transactionHash,
      blockNumberHex: receipt.blockNumber,
      blockNumberDecimal: parseHexQuantity(receipt.blockNumber),
      transactionFound: Boolean(transaction),
      receiptFound: true,
      transaction,
      receipt,
    }, transaction, expectedTransfer);
  }

  if (receipt && receipt.status === '0x0') {
    return withTransferEvidence({
      ...base,
      state: 'failed',
      reason: 'Transaction receipt exists and status is 0x0.',
      transactionHash: receipt.transactionHash,
      blockNumberHex: receipt.blockNumber,
      blockNumberDecimal: parseHexQuantity(receipt.blockNumber),
      transactionFound: Boolean(transaction),
      receiptFound: true,
      transaction,
      receipt,
    }, transaction, expectedTransfer);
  }

  if (transaction && !receipt) {
    return withTransferEvidence({
      ...base,
      state: 'pending',
      reason: 'Transaction was found but no receipt is available yet.',
      transactionHash: transaction.hash,
      transactionFound: true,
      receiptFound: false,
      transaction,
      receipt: null,
    }, transaction, expectedTransfer);
  }

  return withTransferEvidence({
    ...base,
    state: 'unknown',
    reason: 'Transaction hash was not found or receipt status was ambiguous.',
    transactionFound: Boolean(transaction),
    receiptFound: Boolean(receipt),
    transaction,
    receipt,
  }, transaction, expectedTransfer);
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
      `Expected ${ARC_TRANSACTION_STATUS.expectedChainIdHex}; got ${result.chainIdHex || 'unavailable'}.`
    ),
    buildCheck(
      'method-scope',
      'RPC method scope',
      'pass',
      'Used only eth_chainId, eth_getTransactionByHash, and eth_getTransactionReceipt.'
    ),
    buildCheck(
      'wallet',
      'Wallet/signing boundary',
      'pass',
      'No wallet was connected and no transaction was submitted.'
    ),
    buildCheck(
      'state',
      'Status state',
      result.state === 'confirmed' ? 'pass' : result.state === 'failed' ? 'fail' : 'warn',
      result.reason
    ),
    buildCheck(
      'expected-transfer',
      'Expected USDC transfer shape',
      result.transferReview && result.transferReview.state === 'match'
        ? 'pass'
        : result.transferReview && result.transferReview.state === 'mismatch'
          ? 'fail'
          : 'warn',
      result.transferReview ? result.transferReview.reason : 'Expected transfer was not reviewed.'
    ),
    buildCheck(
      'settlement-boundary',
      'Settlement boundary',
      'warn',
      'A receipt and matching calldata do not prove settlement, finality, or business acceptance.'
    ),
  ];
}

function renderChecks(checks) {
  statusCheckList.replaceChildren(
    ...checks.map((item) => {
      const listItem = document.createElement('li');
      listItem.className = item.level;
      const strong = document.createElement('strong');
      strong.textContent = item.level === 'pass' ? 'PASS' : item.level === 'fail' ? 'REVIEW' : 'INFO';
      listItem.append(strong, ` — ${item.label}: ${item.detail}`);
      return listItem;
    })
  );
}

function renderStatus(result, checks) {
  statusPill.textContent = result.state;
  statusPill.className = `status ${result.state}`;
  renderChecks(checks);
  transactionStatusJson.textContent = JSON.stringify(result, null, 2);
}

function renderInitialState() {
  const result = {
    kind: 'arc_testnet_transaction_status',
    state: 'not_checked',
    reason: 'No read-only lookup has run yet.',
    network: ARC_TRANSACTION_STATUS.network,
    rpcUrl: ARC_TRANSACTION_STATUS.rpcUrl,
    expectedChainId: ARC_TRANSACTION_STATUS.expectedChainId,
    expectedChainIdHex: ARC_TRANSACTION_STATUS.expectedChainIdHex,
    evidenceVerdict: 'not_checked',
    settlementProven: false,
    businessAcceptanceProven: false,
    safety: {
      walletConnected: false,
      backendCalls: false,
      readOnlyRpcCheckOnly: true,
      transactionBroadcast: false,
      autonomousSpending: false,
      humanApprovalRequired: true,
      signingRequiresWalletChainGateAndHumanApproval: true,
    },
  };
  renderStatus(result, [
    buildCheck('state', 'Status state', 'warn', 'Paste a transaction hash and run the read-only lookup.'),
    buildCheck('wallet', 'Wallet/signing boundary', 'pass', 'No wallet was connected and no transaction was submitted.'),
  ]);
}

function renderValidationError(hash, reason = 'Transaction hash is not a 32-byte 0x-prefixed value.') {
  const result = {
    kind: 'arc_testnet_transaction_status',
    state: 'unknown',
    reason,
    checkedAt: new Date().toISOString(),
    transactionHash: hash,
    safety: {
      walletConnected: false,
      backendCalls: false,
      readOnlyRpcCheckOnly: true,
      transactionBroadcast: false,
      autonomousSpending: false,
      humanApprovalRequired: true,
      signingRequiresWalletChainGateAndHumanApproval: true,
    },
  };
  renderStatus(result, checksForResult({ ...result, rpcChainIdMatchesArcTestnet: false, chainIdHex: 'not_checked' }, hash));
}

async function checkTransactionStatus() {
  const hash = transactionHashInput.value.trim();
  if (!isValidHash(hash)) {
    renderValidationError(hash);
    return;
  }
  let expectedTransfer;
  try {
    expectedTransfer = buildExpectedTransfer();
  } catch (error) {
    renderValidationError(hash, error.message);
    return;
  }
  statusPill.textContent = 'checking';
  statusPill.className = 'status pending';
  transactionStatusJson.textContent = JSON.stringify({ state: 'checking_arc_rpc', transactionHash: hash }, null, 2);
  try {
    const lookup = await readOnlyLookup(hash);
    const result = classifyTransactionStatus(lookup.chainIdHex, lookup.transaction, lookup.receipt, expectedTransfer, hash);
    renderStatus({ ...result, transactionHash: hash }, checksForResult(result, hash));
  } catch (error) {
    const result = {
      kind: 'arc_testnet_transaction_status',
      state: 'unknown',
      reason: `RPC lookup unavailable: ${error.message}`,
      checkedAt: new Date().toISOString(),
      transactionHash: hash,
      rpcUrl: ARC_TRANSACTION_STATUS.rpcUrl,
      expectedTransfer,
      evidenceVerdict: 'unknown_rpc_unavailable',
      settlementProven: false,
      businessAcceptanceProven: false,
      safety: {
        walletConnected: false,
        backendCalls: false,
        readOnlyRpcCheckOnly: true,
        transactionBroadcast: false,
        autonomousSpending: false,
        humanApprovalRequired: true,
        signingRequiresWalletChainGateAndHumanApproval: true,
      },
    };
    renderStatus(result, checksForResult({ ...result, rpcChainIdMatchesArcTestnet: false, chainIdHex: 'unavailable' }, hash));
  }
}

function resetSample() {
  transactionHashInput.value = SAMPLE_TRANSACTION_HASH;
  expectedRecipientInput.value = '0x1111111111111111111111111111111111111111';
  expectedAmountInput.value = '0.01';
  renderInitialState();
}

checkButton.addEventListener('click', checkTransactionStatus);
resetButton.addEventListener('click', resetSample);
renderInitialState();

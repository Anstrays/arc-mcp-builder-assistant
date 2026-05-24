const transactionHashInput = document.querySelector('#transaction-hash');
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
  walletConnected: false,
  backendCalls: false,
  readOnlyRpcCheckOnly: true,
  transactionBroadcast: false,
  autonomousSpending: false,
  humanApprovalRequired: true,
  signingRequiresWalletChainGateAndHumanApproval: true,
});

const SAMPLE_TRANSACTION_HASH = '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const READ_ONLY_RPC_METHODS = Object.freeze([
  { method: 'eth_chainId', params: [] },
  { method: 'eth_getTransactionByHash', params: ['transactionHash'] },
  { method: 'eth_getTransactionReceipt', params: ['transactionHash'] },
]);

function isValidHash(value) {
  return /^0x[a-fA-F0-9]{64}$/.test(String(value || '').trim());
}

function parseHexQuantity(value) {
  if (typeof value !== 'string' || !/^0x[0-9a-fA-F]+$/.test(value)) return null;
  return Number.parseInt(value, 16);
}

async function rpcCall(method, params = []) {
  const response = await fetch(ARC_TRANSACTION_STATUS.rpcUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
  });
  if (!response.ok) {
    throw new Error(`RPC HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload.error) {
    throw new Error(`${method} failed: ${payload.error.message || JSON.stringify(payload.error)}`);
  }
  return payload.result;
}

async function readOnlyLookup(transactionHash) {
  const chainIdHex = await rpcCall('eth_chainId');
  const transaction = await rpcCall('eth_getTransactionByHash', [transactionHash]);
  const receipt = await rpcCall('eth_getTransactionReceipt', [transactionHash]);
  return { chainIdHex, transaction, receipt };
}

function buildCheck(id, label, level, detail) {
  return { id, label, level, detail };
}

function classifyTransactionStatus(chainIdHex, transaction, receipt) {
  const chainIdDecimal = parseHexQuantity(chainIdHex);
  const chainMatches = chainIdDecimal === ARC_TRANSACTION_STATUS.expectedChainId;
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
    return {
      ...base,
      state: 'unknown',
      reason: 'RPC chain ID did not match Arc Testnet.',
      transactionFound: Boolean(transaction),
      receiptFound: Boolean(receipt),
      transaction,
      receipt,
    };
  }

  if (receipt && receipt.status === '0x1') {
    return {
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
    };
  }

  if (receipt && receipt.status === '0x0') {
    return {
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
    };
  }

  if (transaction && !receipt) {
    return {
      ...base,
      state: 'pending',
      reason: 'Transaction was found but no receipt is available yet.',
      transactionHash: transaction.hash,
      transactionFound: true,
      receiptFound: false,
      transaction,
      receipt: null,
    };
  }

  return {
    ...base,
    state: 'unknown',
    reason: 'Transaction hash was not found or receipt status was ambiguous.',
    transactionFound: Boolean(transaction),
    receiptFound: Boolean(receipt),
    transaction,
    receipt,
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

function renderValidationError(hash) {
  const result = {
    kind: 'arc_testnet_transaction_status',
    state: 'unknown',
    reason: 'Transaction hash is not a 32-byte 0x-prefixed value.',
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
  statusPill.textContent = 'checking';
  statusPill.className = 'status pending';
  transactionStatusJson.textContent = JSON.stringify({ state: 'checking_arc_rpc', transactionHash: hash }, null, 2);
  try {
    const lookup = await readOnlyLookup(hash);
    const result = classifyTransactionStatus(lookup.chainIdHex, lookup.transaction, lookup.receipt);
    renderStatus({ ...result, transactionHash: hash }, checksForResult(result, hash));
  } catch (error) {
    const result = {
      kind: 'arc_testnet_transaction_status',
      state: 'unknown',
      reason: `RPC lookup unavailable: ${error.message}`,
      checkedAt: new Date().toISOString(),
      transactionHash: hash,
      rpcUrl: ARC_TRANSACTION_STATUS.rpcUrl,
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
  renderInitialState();
}

checkButton.addEventListener('click', checkTransactionStatus);
resetButton.addEventListener('click', resetSample);
renderInitialState();

const ARC_TESTNET = Object.freeze({
  name: 'Arc Testnet',
  chainId: 5042002,
  chainIdHex: '0x4cef52',
  rpcUrl: 'https://rpc.testnet.arc.network',
  explorerUrl: 'https://testnet.arcscan.app',
  usdcAddress: '0x3600000000000000000000000000000000000000',
  usdcDecimals: 6,
  nativeGasDecimals: 18,
  maxAmountBaseUnits: 1000000n,
});

const REQUIRED_CONFIRMATION = 'SEND ARC TESTNET USDC';
const FEATURE_GATE_NAME = 'enableArcTestnetSend';
const FEATURE_GATE_VALUE = 'reviewed-testnet-only';
const TRANSFER_SELECTOR = 'a9059cbb';
const ALLOWED_WALLET_METHODS = new Set([
  'eth_requestAccounts',
  'eth_accounts',
  'eth_chainId',
  'wallet_switchEthereumChain',
  'wallet_addEthereumChain',
  'eth_sendTransaction',
]);

const elements = {
  featureGateStatus: document.querySelector('#feature-gate-status'),
  riskAcknowledgement: document.querySelector('#risk-acknowledgement'),
  walletStatus: document.querySelector('#wallet-status'),
  providerState: document.querySelector('#provider-state'),
  accountState: document.querySelector('#account-state'),
  chainState: document.querySelector('#chain-state'),
  connectWallet: document.querySelector('#connect-wallet'),
  switchNetwork: document.querySelector('#switch-network'),
  recipient: document.querySelector('#recipient'),
  amount: document.querySelector('#amount'),
  expiry: document.querySelector('#expiry'),
  memo: document.querySelector('#memo'),
  freezeIntent: document.querySelector('#freeze-intent'),
  intentStatus: document.querySelector('#intent-status'),
  frozenPayload: document.querySelector('#frozen-payload'),
  confirmationPhrase: document.querySelector('#confirmation-phrase'),
  finalSendConfirmation: document.querySelector('#final-send-confirmation'),
  sendTransaction: document.querySelector('#send-transaction'),
  sendStatus: document.querySelector('#send-status'),
  sendResult: document.querySelector('#send-result'),
  transactionLink: document.querySelector('#transaction-link'),
  guardList: document.querySelector('#guard-list'),
  methodLog: document.querySelector('#method-log'),
};

const state = {
  featureGatePresent: new URLSearchParams(window.location.search).get(FEATURE_GATE_NAME) === FEATURE_GATE_VALUE,
  topLevelContext: window.top === window.self,
  provider: window.ethereum || null,
  account: '',
  chainIdHex: '',
  frozenIntent: null,
  frozenDraft: null,
  sendAttempted: false,
  transactionHash: '',
  methodNames: [],
};

function normalizeHex(value) {
  return String(value || '').toLowerCase();
}

function isAddress(value) {
  return /^0x[a-fA-F0-9]{40}$/.test(String(value || '').trim());
}

function isNonZeroAddress(value) {
  return isAddress(value) && !/^0x0{40}$/i.test(String(value || '').trim());
}

function parseUsdcAmount(rawValue) {
  const value = String(rawValue || '').trim();
  if (!/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$/.test(value)) {
    throw new Error('Amount must be a plain positive decimal with at most 6 fractional digits.');
  }
  const [whole, fraction = ''] = value.split('.');
  const baseUnits = (BigInt(whole) * 1000000n) + BigInt(fraction.padEnd(6, '0'));
  if (baseUnits <= 0n) throw new Error('Amount must be greater than zero.');
  if (baseUnits > ARC_TESTNET.maxAmountBaseUnits) throw new Error('Amount exceeds the 1.00 USDC safety cap.');
  return { decimal: value, baseUnits };
}

function encodeTransferCalldata(recipient, amountBaseUnits) {
  const addressWord = recipient.toLowerCase().replace(/^0x/, '').padStart(64, '0');
  const amountWord = amountBaseUnits.toString(16).padStart(64, '0');
  return `0x${TRANSFER_SELECTOR}${addressWord}${amountWord}`;
}

function decodeTransferCalldata(data) {
  const normalized = String(data || '').toLowerCase();
  if (!new RegExp(`^0x${TRANSFER_SELECTOR}[0-9a-f]{128}$`).test(normalized)) {
    throw new Error('Calldata is not the pinned ERC-20 transfer(address,uint256) shape.');
  }
  return {
    method: 'transfer(address,uint256)',
    recipient: `0x${normalized.slice(34, 74)}`,
    amountBaseUnits: BigInt(`0x${normalized.slice(74, 138)}`).toString(),
  };
}

function currentIntent() {
  const recipient = elements.recipient.value.trim().toLowerCase();
  if (!isNonZeroAddress(recipient)) {
    throw new Error('Recipient must be a non-zero 0x-prefixed 20-byte address.');
  }
  if (recipient === ARC_TESTNET.usdcAddress.toLowerCase()) {
    throw new Error('Recipient cannot be the pinned USDC token contract address.');
  }
  const amount = parseUsdcAmount(elements.amount.value);
  const expiryText = elements.expiry.value;
  const expiryMs = Date.parse(expiryText);
  const now = Date.now();
  if (!expiryText || !Number.isFinite(expiryMs) || expiryMs <= now) {
    throw new Error('Expiry must be a valid future time.');
  }
  if (expiryMs > now + (24 * 60 * 60 * 1000)) {
    throw new Error('Expiry must be within 24 hours.');
  }
  const memo = elements.memo.value.trim();
  if (!memo) throw new Error('Memo is required for visible intent binding.');
  if (memo.length > 180) throw new Error('Memo must be 180 characters or fewer.');
  return {
    network: ARC_TESTNET.name,
    chainId: ARC_TESTNET.chainId,
    chainIdHex: ARC_TESTNET.chainIdHex,
    account: state.account.toLowerCase(),
    token: ARC_TESTNET.usdcAddress,
    tokenDecimals: ARC_TESTNET.usdcDecimals,
    recipient,
    amountDecimal: amount.decimal,
    amountBaseUnits: amount.baseUnits.toString(),
    memo,
    expiry: new Date(expiryMs).toISOString(),
  };
}

function buildDraft(intent) {
  const data = encodeTransferCalldata(intent.recipient, BigInt(intent.amountBaseUnits));
  const decoded = decodeTransferCalldata(data);
  return {
    type: 'guarded_arc_testnet_erc20_transfer',
    chainId: ARC_TESTNET.chainIdHex,
    from: intent.account,
    to: ARC_TESTNET.usdcAddress,
    value: '0x0',
    data,
    decoded,
  };
}

function intentMatchesFrozen() {
  if (!state.frozenIntent) return false;
  try {
    return JSON.stringify(currentIntent()) === JSON.stringify(state.frozenIntent);
  } catch (_error) {
    return false;
  }
}

function draftMatchesFrozenIntent() {
  if (!state.frozenIntent || !state.frozenDraft) return false;
  try {
    const rebuilt = buildDraft(state.frozenIntent);
    return (
      JSON.stringify(rebuilt) === JSON.stringify(state.frozenDraft)
      && rebuilt.chainId === ARC_TESTNET.chainIdHex
      && rebuilt.to === ARC_TESTNET.usdcAddress
      && rebuilt.value === '0x0'
      && rebuilt.decoded.recipient === state.frozenIntent.recipient
      && rebuilt.decoded.amountBaseUnits === state.frozenIntent.amountBaseUnits
    );
  } catch (_error) {
    return false;
  }
}

function buildGuardReport() {
  const riskAcknowledged = elements.riskAcknowledgement.checked;
  const providerAvailable = Boolean(state.provider && typeof state.provider.request === 'function');
  const accountValid = isNonZeroAddress(state.account);
  const chainMatches = normalizeHex(state.chainIdHex) === ARC_TESTNET.chainIdHex;
  const phraseMatches = elements.confirmationPhrase.value === REQUIRED_CONFIRMATION;
  const finalChecked = elements.finalSendConfirmation.checked;
  let intentValid = false;
  let intentError = '';
  try {
    currentIntent();
    intentValid = true;
  } catch (error) {
    intentError = error.message;
  }
  const frozen = Boolean(state.frozenIntent && state.frozenDraft);
  const frozenParity = frozen && intentMatchesFrozen() && draftMatchesFrozenIntent();
  const checks = [
    ['feature-gate', state.featureGatePresent, 'Exact reviewed-testnet query gate is present.'],
    ['top-level-context', state.topLevelContext, 'Page is running in a top-level browsing context, not an embedded frame.'],
    ['risk-ack', riskAcknowledged, 'Risk acknowledgement is checked.'],
    ['provider', providerAvailable, 'Injected EVM wallet provider is available.'],
    ['account', accountValid, 'Connected account is a valid EVM address.'],
    ['chain', chainMatches, `Wallet reports Arc Testnet ${ARC_TESTNET.chainIdHex}.`],
    ['intent', intentValid, intentValid ? 'Intent fields are valid.' : intentError],
    ['frozen-parity', frozenParity, 'Current fields and deterministic calldata match the frozen review.'],
    ['typed-confirmation', phraseMatches, 'Exact confirmation phrase matches.'],
    ['final-checkbox', finalChecked, 'Final human confirmation is checked.'],
    ['one-shot-lock', !state.sendAttempted, 'No wallet transaction attempt has occurred this page load.'],
  ];
  return {
    passed: checks.every((check) => check[1]),
    checks: checks.map(([id, passed, detail]) => ({ id, passed, detail })),
  };
}

function canAttemptSend() {
  return buildGuardReport().passed;
}

function recordMethod(method) {
  state.methodNames.push({ method, requestedAt: new Date().toISOString() });
  renderMethodLog();
}

async function requestWallet(request) {
  if (!state.provider || typeof state.provider.request !== 'function') {
    throw new Error('Injected wallet provider is unavailable.');
  }
  if (!ALLOWED_WALLET_METHODS.has(request.method)) {
    throw new Error('Wallet method is outside the reviewed Arc Testnet allowlist.');
  }
  recordMethod(request.method);
  return state.provider.request(request);
}

function safeWalletError(error) {
  const code = Number(error && error.code);
  if (code === 4001) return 'Wallet request was rejected by the user.';
  if (code === 4902) return 'Arc Testnet is not configured in this wallet.';
  if (code === -32002) return 'A wallet request is already pending. Open the wallet extension.';
  return 'Wallet request failed. Review the wallet UI and reload before another send attempt.';
}

function clearFrozenReview(reason) {
  state.frozenIntent = null;
  state.frozenDraft = null;
  elements.finalSendConfirmation.checked = false;
  elements.confirmationPhrase.value = '';
  elements.frozenPayload.textContent = reason;
}

async function connectWallet() {
  if (!state.featureGatePresent || !state.topLevelContext || !elements.riskAcknowledgement.checked) return;
  try {
    const accounts = await requestWallet({ method: 'eth_requestAccounts', params: [] });
    const chainIdHex = await requestWallet({ method: 'eth_chainId', params: [] });
    state.account = Array.isArray(accounts) && isNonZeroAddress(accounts[0]) ? accounts[0] : '';
    state.chainIdHex = normalizeHex(chainIdHex);
    clearFrozenReview('Wallet state changed. Freeze the intent again after reviewing the connected account and chain.');
  } catch (error) {
    elements.sendResult.textContent = safeWalletError(error);
  }
  render();
}

async function switchToArcTestnet() {
  if (!state.featureGatePresent || !state.topLevelContext || !elements.riskAcknowledgement.checked) return;
  try {
    try {
      await requestWallet({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: ARC_TESTNET.chainIdHex }],
      });
    } catch (error) {
      if (Number(error && error.code) !== 4902) throw error;
      await requestWallet({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: ARC_TESTNET.chainIdHex,
          chainName: ARC_TESTNET.name,
          nativeCurrency: { name: 'USDC', symbol: 'USDC', decimals: ARC_TESTNET.nativeGasDecimals },
          rpcUrls: [ARC_TESTNET.rpcUrl],
          blockExplorerUrls: [ARC_TESTNET.explorerUrl],
        }],
      });
    }
    state.chainIdHex = normalizeHex(await requestWallet({ method: 'eth_chainId', params: [] }));
    clearFrozenReview('Network state changed. Freeze the intent again after proving Arc Testnet.');
  } catch (error) {
    elements.sendResult.textContent = safeWalletError(error);
  }
  render();
}

function freezeIntent() {
  try {
    const report = buildGuardReport();
    const prerequisiteIds = ['feature-gate', 'top-level-context', 'risk-ack', 'provider', 'account', 'chain', 'intent'];
    const failedPrerequisite = report.checks.find((check) => prerequisiteIds.includes(check.id) && !check.passed);
    if (failedPrerequisite) {
      throw new Error(failedPrerequisite.detail || 'Resolve the visible intent guards before freezing.');
    }
    state.frozenIntent = currentIntent();
    state.frozenDraft = buildDraft(state.frozenIntent);
    elements.finalSendConfirmation.checked = false;
    elements.confirmationPhrase.value = '';
    elements.frozenPayload.textContent = JSON.stringify({
      intent: state.frozenIntent,
      transactionRequest: state.frozenDraft,
      safety: {
        humanApprovalRequired: true,
        oneAttemptPerPageLoad: true,
        automaticRetry: false,
        retryRule: 'No automatic retry',
        privateKeyHandling: false,
        custody: false,
      },
    }, null, 2);
    elements.sendResult.textContent = 'Intent frozen. Compare every field before final confirmation.';
  } catch (error) {
    clearFrozenReview(error.message);
    elements.sendResult.textContent = error.message;
  }
  render();
}

async function requestOneTransaction() {
  if (!canAttemptSend()) return;
  state.sendAttempted = true;
  render();
  try {
    const liveChain = normalizeHex(await requestWallet({ method: 'eth_chainId', params: [] }));
    const liveAccounts = await requestWallet({ method: 'eth_accounts', params: [] });
    const liveAccount = Array.isArray(liveAccounts) && isNonZeroAddress(liveAccounts[0]) ? liveAccounts[0].toLowerCase() : '';
    if (liveChain !== ARC_TESTNET.chainIdHex || liveAccount !== state.frozenIntent.account) {
      throw new Error('Wallet chain or account changed after review.');
    }
    if (!intentMatchesFrozen() || !draftMatchesFrozenIntent()) {
      throw new Error('Frozen payload parity failed immediately before wallet handoff.');
    }

    const transactionHash = await requestWallet({
      method: 'eth_sendTransaction',
      params: [{
        chainId: state.frozenDraft.chainId,
        from: state.frozenDraft.from,
        to: state.frozenDraft.to,
        value: state.frozenDraft.value,
        data: state.frozenDraft.data,
      }],
    });
    if (!/^0x[a-fA-F0-9]{64}$/.test(String(transactionHash || ''))) {
      throw new Error('Wallet did not return a valid transaction hash.');
    }
    state.transactionHash = transactionHash;
    elements.sendResult.textContent = 'Wallet returned a transaction hash. Status is submitted/pending, not confirmed.';
    elements.transactionLink.href = `${ARC_TESTNET.explorerUrl}/tx/${transactionHash}`;
    elements.transactionLink.hidden = false;
  } catch (error) {
    const internalMessage = error instanceof Error ? error.message : '';
    elements.sendResult.textContent = internalMessage.startsWith('Wallet chain') || internalMessage.startsWith('Frozen payload')
      ? internalMessage
      : safeWalletError(error);
  }
  render();
}

function renderMethodLog() {
  if (!state.methodNames.length) {
    elements.methodLog.replaceChildren(Object.assign(document.createElement('li'), { textContent: 'No wallet methods requested.' }));
    return;
  }
  elements.methodLog.replaceChildren(...state.methodNames.map((entry) => {
    const item = document.createElement('li');
    const code = document.createElement('code');
    code.textContent = entry.method;
    item.append(code, ` at ${entry.requestedAt}`);
    return item;
  }));
}

function renderGuards() {
  const report = buildGuardReport();
  elements.guardList.replaceChildren(...report.checks.map((check) => {
    const item = document.createElement('li');
    const verdict = document.createElement('strong');
    verdict.className = check.passed ? 'pass' : 'fail';
    verdict.textContent = check.passed ? 'PASS' : 'BLOCK';
    item.append(verdict, check.detail);
    return item;
  }));
  return report;
}

function render() {
  const acknowledged = elements.riskAcknowledgement.checked;
  const providerAvailable = Boolean(state.provider && typeof state.provider.request === 'function');
  const chainMatches = normalizeHex(state.chainIdHex) === ARC_TESTNET.chainIdHex;
  const report = renderGuards();

  const reviewEnabled = state.featureGatePresent && state.topLevelContext && acknowledged;
  elements.featureGateStatus.textContent = !state.topLevelContext ? 'blocked in embedded frame' : reviewEnabled ? 'enabled for review' : 'disabled';
  elements.featureGateStatus.className = `status ${reviewEnabled ? 'pass' : 'fail'}`;
  elements.providerState.textContent = providerAvailable ? 'Injected provider detected' : 'No injected provider';
  elements.accountState.textContent = state.account || 'Not requested';
  elements.chainState.textContent = state.chainIdHex || 'Not requested';
  elements.walletStatus.textContent = state.account && chainMatches ? 'Arc Testnet proven' : 'not ready';
  elements.walletStatus.className = `status ${state.account && chainMatches ? 'pass' : 'warn'}`;
  elements.intentStatus.textContent = state.frozenIntent && intentMatchesFrozen() ? 'frozen / parity pass' : 'editable';
  elements.intentStatus.className = `status ${state.frozenIntent && intentMatchesFrozen() ? 'pass' : 'warn'}`;
  elements.sendStatus.textContent = state.transactionHash ? 'submitted / pending' : state.sendAttempted ? 'attempt locked' : report.passed ? 'ready for wallet' : 'blocked';
  elements.sendStatus.className = `status ${state.transactionHash ? 'warn' : report.passed ? 'pass' : 'fail'}`;

  elements.riskAcknowledgement.disabled = !state.featureGatePresent || !state.topLevelContext || state.sendAttempted;
  elements.connectWallet.disabled = !state.featureGatePresent || !state.topLevelContext || !acknowledged || !providerAvailable || state.sendAttempted;
  elements.switchNetwork.disabled = !state.featureGatePresent || !state.topLevelContext || !acknowledged || !providerAvailable || state.sendAttempted;
  elements.freezeIntent.disabled = !state.featureGatePresent || !state.topLevelContext || !acknowledged || !providerAvailable || !state.account || !chainMatches || state.sendAttempted;
  elements.sendTransaction.disabled = !report.passed;
  for (const input of [elements.recipient, elements.amount, elements.expiry, elements.memo, elements.confirmationPhrase, elements.finalSendConfirmation]) {
    input.disabled = state.sendAttempted;
  }
  renderMethodLog();
}

function setDefaultExpiry() {
  const future = new Date(Date.now() + (30 * 60 * 1000));
  const local = new Date(future.getTime() - (future.getTimezoneOffset() * 60000));
  elements.expiry.value = local.toISOString().slice(0, 16);
}

elements.riskAcknowledgement.addEventListener('change', () => {
  if (!elements.riskAcknowledgement.checked) {
    clearFrozenReview('Risk acknowledgement cleared. Freeze and review the intent again.');
  }
  render();
});
elements.connectWallet.addEventListener('click', connectWallet);
elements.switchNetwork.addEventListener('click', switchToArcTestnet);
elements.freezeIntent.addEventListener('click', freezeIntent);
elements.sendTransaction.addEventListener('click', requestOneTransaction);
for (const input of [elements.recipient, elements.amount, elements.expiry, elements.memo, elements.confirmationPhrase, elements.finalSendConfirmation]) {
  input.addEventListener('input', render);
  input.addEventListener('change', render);
}

if (state.provider && typeof state.provider.on === 'function') {
  state.provider.on('accountsChanged', (accounts) => {
    state.account = Array.isArray(accounts) && isNonZeroAddress(accounts[0]) ? accounts[0] : '';
    clearFrozenReview('Wallet account changed. Freeze and review the intent again.');
    render();
  });
  state.provider.on('chainChanged', (chainIdHex) => {
    state.chainIdHex = normalizeHex(chainIdHex);
    clearFrozenReview('Wallet network changed. Freeze and review the intent again.');
    render();
  });
}

if (typeof window.addEventListener === 'function') {
  window.addEventListener('beforeunload', (event) => {
    if (state.transactionHash) {
      event.preventDefault();
      event.returnValue = 'A wallet transaction has been submitted and may still be pending. Leave anyway?';
    }
  });
}

setDefaultExpiry();
render();

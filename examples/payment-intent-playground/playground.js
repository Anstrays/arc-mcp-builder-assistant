const form = document.querySelector('#intent-form');
const jsonOutput = document.querySelector('#intent-json');
const statusPill = document.querySelector('#status-pill');
const statusLog = document.querySelector('#status-log');
const prepareButton = document.querySelector('#prepare');
const approveButton = document.querySelector('#approve');
const submitButton = document.querySelector('#submit');
const resetButton = document.querySelector('#reset');
const arcChainId = document.querySelector('#arc-chain-id');
const arcRpcUrl = document.querySelector('#arc-rpc-url');
const arcReadonlyState = document.querySelector('#arc-readonly-state');
const arcSafetyJson = document.querySelector('#arc-safety-json');
const walletGuardReasons = document.querySelector('#wallet-guard-reasons');
const walletProviderState = document.querySelector('#wallet-provider-state');
const walletAddressState = document.querySelector('#wallet-address-state');
const walletChainState = document.querySelector('#wallet-chain-state');
const validationSummaryList = document.querySelector('#validation-summary-list');
const statusStateList = document.querySelector('#status-state-list');
const signingPreflightReport = document.querySelector('#signing-preflight-report');
const copyPreflightButton = document.querySelector('#copy-preflight-report');
const erc20BaseUnits = document.querySelector('#erc20-base-units');
const erc20Decimals = document.querySelector('#erc20-decimals');
const nativeGasDecimals = document.querySelector('#native-gas-decimals');

const ARC_TESTNET_STATUS = Object.freeze({
  network: 'Arc Testnet',
  expectedChainIdDecimal: 5042002,
  expectedChainIdHex: '0x4cef52',
  rpcUrl: 'https://rpc.testnet.arc.network',
  explorerUrl: 'https://testnet.arcscan.app',
  erc20UsdcAddress: '0x3600000000000000000000000000000000000000',
  erc20UsdcDecimals: 6,
  nativeGasAsset: 'USDC',
  nativeGasDecimals: 18,
  statusSource: 'static Arc docs constants + read-only helper baseline',
  walletConnected: false,
  backendCalls: false,
  transactionBroadcast: false,
  signingRequiresWalletChainGateAndHumanApproval: true,
});

const STATUS_STATES = Object.freeze([
  {
    id: 'draft',
    label: 'Draft',
    description: 'Intent exists but is not approved.',
  },
  {
    id: 'ready_for_review',
    label: 'Ready for review',
    description: 'Fields are valid enough for human review.',
  },
  {
    id: 'approved_local',
    label: 'Approved locally',
    description: 'Human approved the local exercise only.',
  },
  {
    id: 'blocked_wallet_unavailable',
    label: 'Wallet blocked',
    description: 'Signing remains disabled by guardrails.',
  },
]);

const initialEvents = [
  ['draft', 'Playground loaded with local-only defaults.'],
];

let currentStatus = 'draft';
let events = [...initialEvents];
let frozenIntentSnapshot = null;

function readIntent() {
  const data = new FormData(form);
  const intent = {
    agent: String(data.get('agent') || '').trim(),
    recipient: String(data.get('recipient') || '').trim(),
    asset: String(data.get('asset') || 'USDC').trim(),
    amount: String(data.get('amount') || '').trim(),
    memo: String(data.get('memo') || '').trim(),
    expiry: String(data.get('expiry') || '').trim(),
    status: currentStatus,
    networkReadiness: {
      chainId: ARC_TESTNET_STATUS.expectedChainIdDecimal,
      chainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex,
      rpcUrl: ARC_TESTNET_STATUS.rpcUrl,
      explorerUrl: ARC_TESTNET_STATUS.explorerUrl,
      assetAddress: ARC_TESTNET_STATUS.erc20UsdcAddress,
      assetDecimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
      nativeGasDecimals: ARC_TESTNET_STATUS.nativeGasDecimals,
      statusSource: ARC_TESTNET_STATUS.statusSource,
    },
    safety: {
      walletConnected: false,
      backendCalls: false,
      autonomousSpending: false,
      humanApprovalRequired: true,
      walletPreviewOnly: true,
      walletAdapterFeatureFlag: false,
    },
  };

  return {
    ...intent,
    unitPreview: buildUnitPreview(intent),
  };
}

function appendEvent(status, message) {
  currentStatus = status;
  logEvent(status, message);
}

function logEvent(status, message) {
  events = [[status, message], ...events].slice(0, 8);
  render();
}

function renderArcStatusPanel() {
  arcChainId.textContent = `${ARC_TESTNET_STATUS.expectedChainIdDecimal} (${ARC_TESTNET_STATUS.expectedChainIdHex})`;
  arcRpcUrl.textContent = ARC_TESTNET_STATUS.rpcUrl;
  arcReadonlyState.textContent = ARC_TESTNET_STATUS.transactionBroadcast
    ? 'Broadcast enabled'
    : 'Read-only / no broadcast';
  arcSafetyJson.textContent = JSON.stringify(ARC_TESTNET_STATUS, null, 2);
}

function hasValidRecipient(recipient) {
  return /^0x[a-fA-F0-9]{40}$/.test(recipient);
}

function hasValidUsdcAmount(amount) {
  return /^(?:0|[1-9]\d*)(?:\.\d{1,6})?$/.test(amount) && Number(amount) > 0;
}

function formatUsdcBaseUnits(amount) {
  const normalizedAmount = String(amount || '').trim();
  if (!hasValidUsdcAmount(normalizedAmount)) return 'invalid';

  const [whole, fraction = ''] = normalizedAmount.split('.');
  const paddedFraction = fraction.padEnd(ARC_TESTNET_STATUS.erc20UsdcDecimals, '0');
  const scale = 10n ** BigInt(ARC_TESTNET_STATUS.erc20UsdcDecimals);
  return String((BigInt(whole) * scale) + BigInt(paddedFraction));
}

function buildUnitPreview(intent) {
  return {
    baseUnits: formatUsdcBaseUnits(intent.amount),
    erc20Decimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
    nativeGasDecimals: ARC_TESTNET_STATUS.nativeGasDecimals,
    warning: 'Do not use native gas decimals for ERC-20 USDC transfer amounts.',
    localOnly: true,
  };
}

function renderUnitPreview(intent) {
  const preview = buildUnitPreview(intent);
  erc20BaseUnits.textContent = preview.baseUnits;
  erc20Decimals.textContent = String(preview.erc20Decimals);
  nativeGasDecimals.textContent = String(preview.nativeGasDecimals);
}

function hasFutureExpiry(expiry) {
  if (!expiry) return false;
  const expiryTime = new Date(expiry).getTime();
  return Number.isFinite(expiryTime) && expiryTime > Date.now();
}

function normalizeIntentForFreeze(intent) {
  return JSON.stringify({
    recipient: intent.recipient,
    asset: intent.asset,
    amount: intent.amount,
    memo: intent.memo,
    expiry: intent.expiry,
    chainId: ARC_TESTNET_STATUS.expectedChainIdDecimal,
    assetAddress: ARC_TESTNET_STATUS.erc20UsdcAddress,
    assetDecimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
    baseUnits: formatUsdcBaseUnits(intent.amount),
  });
}

function freezeIntentForReview(intent) {
  frozenIntentSnapshot = {
    frozenAt: new Date().toISOString(),
    normalizedIntent: normalizeIntentForFreeze(intent),
    fields: {
      recipient: intent.recipient,
      asset: intent.asset,
      amount: intent.amount,
      memo: intent.memo,
      expiry: intent.expiry,
      chainId: ARC_TESTNET_STATUS.expectedChainIdDecimal,
      chainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex,
      assetAddress: ARC_TESTNET_STATUS.erc20UsdcAddress,
      assetDecimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
      baseUnits: formatUsdcBaseUnits(intent.amount),
    },
  };
}

function hasFrozenIntentChanged(intent) {
  if (!frozenIntentSnapshot) return false;
  return frozenIntentSnapshot.normalizedIntent !== normalizeIntentForFreeze(intent);
}

function getInjectedWalletProvider() {
  return globalThis.ethereum || null;
}

function getWalletPreviewState(intent) {
  const provider = getInjectedWalletProvider();
  const chainId = provider && typeof provider.chainId === 'string' ? provider.chainId.toLowerCase() : null;
  const selectedAddress = provider && typeof provider.selectedAddress === 'string' ? provider.selectedAddress : '';
  const chainMatches = chainId === ARC_TESTNET_STATUS.expectedChainIdHex;
  return {
    mode: 'read-only wallet preview',
    providerDetected: Boolean(provider),
    requestMethodsCalled: false,
    selectedAddress: selectedAddress || null,
    connectedAddressKnown: hasValidRecipient(selectedAddress),
    observedChainIdHex: chainId,
    expectedChainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex,
    expectedChainIdDecimal: ARC_TESTNET_STATUS.expectedChainIdDecimal,
    chainMatches,
    frozenIntentPresent: Boolean(frozenIntentSnapshot),
    frozenIntentChanged: hasFrozenIntentChanged(intent),
    walletActionEnabled: false,
  };
}

function getWalletGuardReasons(intent) {
  const reasons = [
    'Wrong chain: expected Arc Testnet chain ID 5042002 (0x4cef52).',
    'RPC unavailable: no live browser RPC probe is enabled in this local-only demo.',
    'Unverified docs/constants: re-check Arc MCP/docs before any signing PR.',
    'User approval required: real signing must open an external wallet confirmation.',
    'Wallet adapter feature flag is off: this UI only previews provider/address/chain state.',
  ];

  if (!hasValidRecipient(intent.recipient)) {
    reasons.push('Missing recipient: enter a 0x-prefixed Arc Testnet recipient before review.');
  }
  if (!hasValidUsdcAmount(intent.amount)) {
    reasons.push('Invalid amount or decimals: use a positive USDC amount with at most 6 decimal places.');
  }
  if (!hasFutureExpiry(intent.expiry)) {
    reasons.push('Expired intent: choose a future expiry before enabling wallet review.');
  }
  const walletPreview = getWalletPreviewState(intent);
  if (!walletPreview.providerDetected) {
    reasons.push('Wallet provider not detected: no injected browser wallet was observed.');
  } else if (!walletPreview.connectedAddressKnown) {
    reasons.push('Wallet account unknown: this guard does not request accounts or permissions.');
  }
  if (walletPreview.observedChainIdHex && !walletPreview.chainMatches) {
    reasons.push(`Wrong wallet chain observed: expected ${ARC_TESTNET_STATUS.expectedChainIdHex}, saw ${walletPreview.observedChainIdHex}.`);
  }
  if (walletPreview.frozenIntentChanged) {
    reasons.push('Frozen intent changed: restart review before any future wallet action.');
  }

  return reasons;
}

function renderWalletGuardPanel(intent) {
  const walletPreview = getWalletPreviewState(intent);
  walletProviderState.textContent = walletPreview.providerDetected ? 'Detected / read-only' : 'Not detected';
  walletAddressState.textContent = walletPreview.selectedAddress || 'Not requested';
  walletChainState.textContent = walletPreview.chainMatches ? 'Arc Testnet observed / still disabled' : 'Blocked';
  const reasons = getWalletGuardReasons(intent);
  walletGuardReasons.replaceChildren(
    ...reasons.map((reason) => {
      const item = document.createElement('li');
      item.textContent = reason;
      return item;
    })
  );
}

function isIntentReadyForReview(intent) {
  return hasValidRecipient(intent.recipient)
    && hasValidUsdcAmount(intent.amount)
    && hasFutureExpiry(intent.expiry);
}

function nextStatusAfterPrepare(intent) {
  return isIntentReadyForReview(intent) ? 'ready_for_review' : 'draft';
}

function markStatusStep(currentStatusId) {
  const knownStatuses = new Set(STATUS_STATES.map((status) => status.id));
  const safeStatusId = knownStatuses.has(currentStatusId) ? currentStatusId : 'draft';

  statusStateList.querySelectorAll('[data-status-step]').forEach((item) => {
    const isActive = item.dataset.statusStep === safeStatusId;
    item.classList.toggle('active', isActive);
    item.setAttribute('aria-current', isActive ? 'step' : 'false');
  });
}

function buildValidationSummary(intent) {
  return [
    {
      id: 'recipient',
      label: 'Recipient format',
      passed: hasValidRecipient(intent.recipient),
      detail: hasValidRecipient(intent.recipient)
        ? '0x recipient shape is valid.'
        : 'Use a 0x-prefixed address with 40 hex characters.',
    },
    {
      id: 'amount',
      label: 'USDC amount',
      passed: hasValidUsdcAmount(intent.amount),
      detail: hasValidUsdcAmount(intent.amount)
        ? 'Positive amount with at most 6 decimals.'
        : 'Use a positive USDC amount with at most 6 decimals.',
    },
    {
      id: 'expiry',
      label: 'Future expiry',
      passed: hasFutureExpiry(intent.expiry),
      detail: hasFutureExpiry(intent.expiry)
        ? 'Expiry is still in the future.'
        : 'Choose a future expiry before wallet review.',
    },
    {
      id: 'approval',
      label: 'Human approval marker',
      passed: currentStatus === 'approved_local',
      detail: currentStatus === 'approved_local'
        ? 'Local approval marker is present.'
        : 'Click Approve manually after reviewing the intent.',
    },
  ];
}

function renderValidationSummary(intent) {
  validationSummaryList.replaceChildren(
    ...buildValidationSummary(intent).map((check) => {
      const item = document.createElement('li');
      const strong = document.createElement('strong');
      strong.textContent = `${check.passed ? 'PASS' : 'BLOCK'} · ${check.label}`;
      item.append(strong, document.createTextNode(` — ${check.detail}`));
      return item;
    })
  );
}

function buildSigningPreflightReport(intent) {
  return {
    walletAction: 'blocked',
    nextRequiredReview: 'separate testnet-only wallet PR',
    generatedFrom: 'browser-local intent state only',
    guardReasons: getWalletGuardReasons(intent),
    unitPreview: buildUnitPreview(intent),
    validationSummary: buildValidationSummary(intent),
    walletPreview: getWalletPreviewState(intent),
    frozenIntent: frozenIntentSnapshot ? frozenIntentSnapshot.fields : null,
    checks: {
      chainGate: {
        expectedChainId: ARC_TESTNET_STATUS.expectedChainIdDecimal,
        expectedChainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex,
        passed: false,
        note: 'No live wallet chain check is performed in this playground.',
      },
      recipientFormat: {
        passed: hasValidRecipient(intent.recipient),
        value: intent.recipient || null,
      },
      amountFormat: {
        passed: hasValidUsdcAmount(intent.amount),
        value: intent.amount || null,
        decimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
      },
      expiryWindow: {
        passed: hasFutureExpiry(intent.expiry),
        value: intent.expiry || null,
      },
      frozenIntent: {
        passed: Boolean(frozenIntentSnapshot) && !hasFrozenIntentChanged(intent),
        present: Boolean(frozenIntentSnapshot),
        changedAfterFreeze: hasFrozenIntentChanged(intent),
        note: 'Future wallet PRs must sign exactly the frozen reviewed fields.',
      },
      humanApproval: {
        passed: currentStatus === 'approved_local',
        required: true,
        note: 'Local approval is only a review marker, not wallet consent.',
      },
    },
  };
}

function renderSigningPreflightReport(intent) {
  signingPreflightReport.textContent = serializeSigningPreflightReport(intent);
}

function serializeSigningPreflightReport(intent) {
  return JSON.stringify(buildSigningPreflightReport(intent), null, 2);
}

async function copySigningPreflightReport() {
  const intent = readIntent();
  const reportText = serializeSigningPreflightReport(intent);

  if (!navigator.clipboard || !navigator.clipboard.writeText) {
    signingPreflightReport.focus();
    logEvent('copy_unavailable', 'Clipboard copy was unavailable; select and copy the report manually.');
    return;
  }

  try {
    await navigator.clipboard.writeText(reportText);
    logEvent('copied_preflight_report', 'Signing preflight report was copied locally. No wallet or network call was made.');
  } catch (error) {
    signingPreflightReport.focus();
    logEvent('copy_unavailable', 'Clipboard copy was unavailable; select and copy the report manually.');
  }
}

function render() {
  const intent = readIntent();
  jsonOutput.textContent = JSON.stringify(intent, null, 2);
  statusPill.textContent = currentStatus;
  renderWalletGuardPanel(intent);
  renderUnitPreview(intent);
  renderValidationSummary(intent);
  renderSigningPreflightReport(intent);
  markStatusStep(currentStatus);
  statusLog.replaceChildren(
    ...events.map(([status, message]) => {
      const row = document.createElement('div');
      const strong = document.createElement('strong');
      strong.textContent = status;
      row.append(strong, document.createTextNode(` · ${message}`));
      return row;
    })
  );
}

form.addEventListener('input', () => {
  render();
});

prepareButton.addEventListener('click', () => {
  const intent = readIntent();
  const nextStatus = nextStatusAfterPrepare(intent);
  if (nextStatus === 'ready_for_review') {
    freezeIntentForReview(intent);
    appendEvent('ready_for_review', 'Agent prepared and froze a reviewable intent object. No wallet prompt was opened.');
    return;
  }
  appendEvent('draft', 'Intent needs valid recipient, amount, and future expiry before review.');
});

approveButton.addEventListener('click', () => {
  const intent = readIntent();
  if (!frozenIntentSnapshot || hasFrozenIntentChanged(intent)) {
    appendEvent('draft', 'Approval blocked until the current intent is prepared and frozen again.');
    return;
  }
  appendEvent('approved_local', 'Human approval was recorded as local UI state only for the frozen intent.');
});

submitButton.addEventListener('click', () => {
  appendEvent('blocked_wallet_unavailable', 'Wallet submission stayed blocked. No transaction was broadcast.');
});

copyPreflightButton.addEventListener('click', () => {
  copySigningPreflightReport();
});

resetButton.addEventListener('click', () => {
  currentStatus = 'draft';
  events = [...initialEvents];
  frozenIntentSnapshot = null;
  form.reset();
  render();
});

renderArcStatusPanel();
render();

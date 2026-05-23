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
const validationSummaryList = document.querySelector('#validation-summary-list');
const signingPreflightReport = document.querySelector('#signing-preflight-report');
const copyPreflightButton = document.querySelector('#copy-preflight-report');

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

const initialEvents = [
  ['draft', 'Playground loaded with local-only defaults.'],
];

let currentStatus = 'draft';
let events = [...initialEvents];

function readIntent() {
  const data = new FormData(form);
  return {
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
    },
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

function hasFutureExpiry(expiry) {
  if (!expiry) return false;
  const expiryTime = new Date(expiry).getTime();
  return Number.isFinite(expiryTime) && expiryTime > Date.now();
}

function getWalletGuardReasons(intent) {
  const reasons = [
    'Wrong chain: expected Arc Testnet chain ID 5042002 (0x4cef52).',
    'RPC unavailable: no live browser RPC probe is enabled in this local-only demo.',
    'Unverified docs/constants: re-check Arc MCP/docs before any signing PR.',
    'User approval required: real signing must open an external wallet confirmation.',
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

  return reasons;
}

function renderWalletGuardPanel(intent) {
  const reasons = getWalletGuardReasons(intent);
  walletGuardReasons.replaceChildren(
    ...reasons.map((reason) => {
      const item = document.createElement('li');
      item.textContent = reason;
      return item;
    })
  );
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
      passed: currentStatus === 'approved_locally',
      detail: currentStatus === 'approved_locally'
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
    validationSummary: buildValidationSummary(intent),
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
      humanApproval: {
        passed: currentStatus === 'approved_locally',
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
  renderValidationSummary(intent);
  renderSigningPreflightReport(intent);
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
  appendEvent('pending_human_approval', 'Agent prepared a reviewable intent object. No wallet prompt was opened.');
});

approveButton.addEventListener('click', () => {
  appendEvent('approved_locally', 'Human approval was recorded as local UI state only.');
});

submitButton.addEventListener('click', () => {
  appendEvent('submitted_simulation', 'Submission was simulated locally. No transaction was broadcast.');
});

copyPreflightButton.addEventListener('click', () => {
  copySigningPreflightReport();
});

resetButton.addEventListener('click', () => {
  currentStatus = 'draft';
  events = [...initialEvents];
  form.reset();
  render();
});

renderArcStatusPanel();
render();

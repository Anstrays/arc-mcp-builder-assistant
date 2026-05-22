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

const ARC_TESTNET_STATUS = Object.freeze({
  network: 'Arc Testnet',
  expectedChainIdDecimal: 5042002,
  expectedChainIdHex: '0x4cef52',
  rpcUrl: 'https://rpc.testnet.arc.network',
  nativeGasAsset: 'USDC',
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

function render() {
  const intent = readIntent();
  jsonOutput.textContent = JSON.stringify(intent, null, 2);
  statusPill.textContent = currentStatus;
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

resetButton.addEventListener('click', () => {
  currentStatus = 'draft';
  events = [...initialEvents];
  form.reset();
  render();
});

renderArcStatusPanel();
render();

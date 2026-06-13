const ARC_COMPONENT_EXPECTATIONS = Object.freeze({
  network: 'arc-testnet',
  chainId: 5042002,
  chainIdHex: '0x4cef52',
  nativeGasAsset: 'USDC',
  nativeGasDecimals: 18,
  erc20UsdcAddress: '0x3600000000000000000000000000000000000000',
  erc20UsdcDecimals: 6,
});

const fields = {
  agentName: document.querySelector('#agent-name'),
  agentRole: document.querySelector('#agent-role'),
  purpose: document.querySelector('#purpose'),
  amount: document.querySelector('#amount'),
  recipient: document.querySelector('#recipient'),
  reviewNote: document.querySelector('#review-note'),
};
const cards = {
  agent: document.querySelector('#agent-card'),
  payment: document.querySelector('#payment-card'),
  receipt: document.querySelector('#receipt-card'),
  combined: document.querySelector('#components-json'),
  events: document.querySelector('#event-log'),
  status: document.querySelector('#status-pill'),
};
const buttons = {
  freeze: document.querySelector('#freeze-request'),
  approve: document.querySelector('#mark-approved'),
  receipt: document.querySelector('#mark-receipt'),
  reset: document.querySelector('#reset-components'),
};

let status = 'draft';
let frozenAt = null;
let approvedAt = null;
let receiptAt = null;
let events = [];

function nowIso() {
  return new Date().toISOString();
}

function amountIsValid(value) {
  return /^(?:0|[1-9]\d*)(?:\.\d{1,2})?$/.test(String(value || '').trim())
    && Number(value) > 0;
}

function recipientIsValid(value) {
  return /^0x[a-fA-F0-9]{40}$/.test(String(value || '').trim())
    && !/^0x0{40}$/i.test(String(value || '').trim());
}

function normalizedAmount() {
  return amountIsValid(fields.amount.value) ? Number(fields.amount.value).toFixed(2) : '0.00';
}

function addEvent(event, actor = 'system') {
  events = [...events, {
    at: nowIso(),
    actor,
    event,
    requiresHumanReview: true,
    walletActionEnabled: false,
    transactionBroadcast: false,
  }];
}

function agentCard() {
  return {
    agentId: `${fields.agentRole.value}.local`,
    displayName: fields.agentName.value.trim(),
    role: fields.agentRole.value,
    trustLevel: 'unverified-local-demo',
    sourceNotes: 'Review Arc docs/MCP context before claiming production capability.',
    walletAuthority: false,
    custodyAuthority: false,
  };
}

function paymentRequestCard() {
  return {
    intentId: 'intent-local-components-001',
    purpose: fields.purpose.value.trim(),
    recipient: fields.recipient.value.trim(),
    amount: normalizedAmount(),
    asset: 'USDC',
    assetDecimals: ARC_COMPONENT_EXPECTATIONS.erc20UsdcDecimals,
    network: ARC_COMPONENT_EXPECTATIONS.network,
    chainId: ARC_COMPONENT_EXPECTATIONS.chainId,
    expiresAt: 'review-before-wallet-handoff',
    frozenAt,
    humanApprovalRequired: true,
    moneyFieldsFrozenBeforeWallet: Boolean(frozenAt),
  };
}

function receiptCard() {
  return {
    receiptId: 'receipt-local-components-001',
    intentId: paymentRequestCard().intentId,
    status: receiptAt ? 'simulated' : approvedAt ? 'approved_local_no_broadcast' : 'not_checked',
    transactionHash: null,
    explorerUrl: null,
    checkedAt: receiptAt,
    checks: [
      { field: 'chainId', expected: ARC_COMPONENT_EXPECTATIONS.chainId, passed: true },
      { field: 'asset', expected: 'USDC', passed: true },
      { field: 'humanApprovalRequired', expected: true, passed: true },
      { field: 'transactionBroadcast', expected: false, passed: true },
    ],
    transactionBroadcast: false,
  };
}

function combinedObject() {
  return {
    schema: 'arc-mcp-builder-assistant.agentCommerce.components.v1',
    status,
    network: ARC_COMPONENT_EXPECTATIONS,
    agent: agentCard(),
    paymentRequest: paymentRequestCard(),
    receipt: receiptCard(),
    review: {
      note: fields.reviewNote.value.trim(),
      humanApprovalRequired: true,
      localOnly: true,
      walletConnected: false,
      walletActionEnabled: false,
      signingEnabled: false,
      transactionBroadcast: false,
      backendCalls: false,
      mainnetEnabled: false,
    },
    events,
  };
}

function render() {
  const moneyFieldsFrozen = status !== 'draft';
  cards.status.textContent = status === 'draft' ? 'Draft review object' : status === 'frozen' ? 'Money fields frozen' : status === 'approved' ? 'Local approval recorded' : 'Simulated receipt added';
  cards.agent.textContent = JSON.stringify(agentCard(), null, 2);
  cards.payment.textContent = JSON.stringify(paymentRequestCard(), null, 2);
  cards.receipt.textContent = JSON.stringify(receiptCard(), null, 2);
  cards.combined.textContent = JSON.stringify(combinedObject(), null, 2);
  cards.events.replaceChildren(...events.map((entry) => {
    const li = document.createElement('li');
    li.textContent = `${entry.actor}: ${entry.event} · ${entry.at}`;
    return li;
  }));
  for (const field of [fields.purpose, fields.amount, fields.recipient]) {
    field.disabled = moneyFieldsFrozen;
  }
  buttons.freeze.disabled = status !== 'draft'
    || !amountIsValid(fields.amount.value)
    || !recipientIsValid(fields.recipient.value);
  buttons.approve.disabled = status !== 'frozen';
  buttons.receipt.disabled = status !== 'approved';
}

function reset() {
  status = 'draft';
  frozenAt = null;
  approvedAt = null;
  receiptAt = null;
  events = [{
    at: nowIso(),
    actor: 'system',
    event: 'Draft local component object created',
    requiresHumanReview: true,
    walletActionEnabled: false,
    transactionBroadcast: false,
  }];
  render();
}

buttons.freeze.addEventListener('click', () => {
  status = 'frozen';
  frozenAt = nowIso();
  addEvent('Human froze payment request fields before wallet handoff', 'human');
  render();
});
buttons.approve.addEventListener('click', () => {
  status = 'approved';
  approvedAt = nowIso();
  addEvent('Human recorded local approval; no wallet action was enabled', 'human');
  render();
});
buttons.receipt.addEventListener('click', () => {
  status = 'receipt_simulated';
  receiptAt = nowIso();
  addEvent('System added simulated receipt card without transaction broadcast', 'system');
  render();
});
buttons.reset.addEventListener('click', reset);
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
  field.addEventListener('change', render);
}
reset();

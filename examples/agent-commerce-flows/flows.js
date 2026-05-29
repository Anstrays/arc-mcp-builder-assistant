const ARC_FLOW_EXPECTATIONS = Object.freeze({
  network: 'arc-testnet',
  chainId: 5042002,
  chainIdHex: '0x4cef52',
  nativeGasAsset: 'USDC',
  nativeGasDecimals: 18,
  erc20UsdcAddress: '0x3600000000000000000000000000000000000000',
  erc20UsdcDecimals: 6,
});

const FLOW_TEMPLATES = Object.freeze({
  'paid-api-call': {
    title: 'Paid API call',
    description: 'A research agent asks to buy one paid data response under a human-reviewed cost cap.',
    agentName: 'Research Buyer Agent',
    agentRole: 'paid-api-gateway',
    recipient: '0x0000000000000000000000000000000000000000',
    amount: '1.25',
    purpose: 'Buy one market-data response for a cited report',
    evidence: 'Reviewer checks endpoint purpose, quote, recipient, amount, and freshness before any future x402/Gateway proof path.',
    receiptStatus: 'api_response_release_simulated',
  },
  'creator-payout': {
    title: 'Creator payout',
    description: 'A project lead reviews a contributor payout line item before any stablecoin settlement work.',
    agentName: 'Payout Review Agent',
    agentRole: 'creator-payout-agent',
    recipient: '0x1111111111111111111111111111111111111111',
    amount: '75.00',
    purpose: 'Pay contributor for edited Arc builder demo clip',
    evidence: 'Reviewer checks deliverable URL, contributor identity, payout reason, and amount before any future wallet handoff.',
    receiptStatus: 'payout_note_simulated',
  },
  'ai-agent-commerce': {
    title: 'AI-agent commerce',
    description: 'One agent requests a specialist agent action under a user-approved spend cap.',
    agentName: 'Coordinator Agent',
    agentRole: 'agent-to-agent-coordinator',
    recipient: '0x2222222222222222222222222222222222222222',
    amount: '3.50',
    purpose: 'Call specialist code-review agent for one bounded review task',
    evidence: 'Reviewer checks specialist trust notes, quoted task, cap, and receipt expectations before any future paid-agent proof path.',
    receiptStatus: 'specialist_output_simulated',
  },
});

const fields = {
  agentName: document.querySelector('#agent-name'),
  recipient: document.querySelector('#recipient'),
  amount: document.querySelector('#amount'),
  purpose: document.querySelector('#purpose'),
  evidence: document.querySelector('#evidence'),
};
const nodes = {
  title: document.querySelector('#selected-title'),
  description: document.querySelector('#selected-description'),
  nav: document.querySelector('#flow-nav'),
  status: document.querySelector('#flow-status'),
  agent: document.querySelector('#agent-json'),
  request: document.querySelector('#request-json'),
  receipt: document.querySelector('#receipt-json'),
  events: document.querySelector('#event-log'),
  combined: document.querySelector('#flow-json'),
};
const buttons = {
  freeze: document.querySelector('#freeze-flow'),
  approve: document.querySelector('#approve-flow'),
  receipt: document.querySelector('#simulate-receipt'),
  reset: document.querySelector('#reset-flow'),
};

let selectedFlowId = 'paid-api-call';
let state = 'draft_review';
let frozenAt = null;
let approvedAt = null;
let receiptAt = null;
let events = [];

function nowIso() {
  return new Date().toISOString();
}

function activeTemplate() {
  return FLOW_TEMPLATES[selectedFlowId];
}

function normalizedAmount() {
  const parsed = Number(fields.amount.value || 0);
  if (!Number.isFinite(parsed) || parsed < 0) return '0.00';
  return parsed.toFixed(2);
}

function addEvent(event, actor = 'system') {
  events = [...events, {
    at: nowIso(),
    actor,
    event,
    humanApprovalRequired: true,
    walletActionEnabled: false,
    transactionBroadcast: false,
  }];
}

function loadFlow(flowId) {
  selectedFlowId = flowId;
  const flow = activeTemplate();
  fields.agentName.value = flow.agentName;
  fields.recipient.value = flow.recipient;
  fields.amount.value = flow.amount;
  fields.purpose.value = flow.purpose;
  fields.evidence.value = flow.evidence;
  state = 'draft_review';
  frozenAt = null;
  approvedAt = null;
  receiptAt = null;
  events = [{
    at: nowIso(),
    actor: 'system',
    event: `${flow.title} local flow loaded`,
    humanApprovalRequired: true,
    walletActionEnabled: false,
    transactionBroadcast: false,
  }];
  render();
}

function agentObject() {
  const flow = activeTemplate();
  return {
    agentId: `${selectedFlowId}.local`,
    displayName: fields.agentName.value.trim(),
    role: flow.agentRole,
    trustLevel: 'unverified-local-demo',
    sourceNotes: fields.evidence.value.trim(),
    walletAuthority: false,
    custodyAuthority: false,
  };
}

function requestObject() {
  return {
    intentId: `intent-${selectedFlowId}-001`,
    flowId: selectedFlowId,
    purpose: fields.purpose.value.trim(),
    recipient: fields.recipient.value.trim(),
    amount: normalizedAmount(),
    asset: 'USDC',
    assetDecimals: ARC_FLOW_EXPECTATIONS.erc20UsdcDecimals,
    network: ARC_FLOW_EXPECTATIONS.network,
    chainId: ARC_FLOW_EXPECTATIONS.chainId,
    expiresAt: 'review-before-wallet-handoff',
    humanApprovalRequired: true,
    frozenBeforeWallet: Boolean(frozenAt),
    frozenAt,
  };
}

function receiptObject() {
  const flow = activeTemplate();
  return {
    receiptId: `receipt-${selectedFlowId}-001`,
    intentId: requestObject().intentId,
    status: receiptAt ? flow.receiptStatus : approvedAt ? 'approved_local_no_broadcast' : 'not_checked',
    transactionHash: null,
    explorerUrl: null,
    checkedAt: receiptAt,
    checks: [
      { field: 'flowId', expected: selectedFlowId, passed: true },
      { field: 'chainId', expected: ARC_FLOW_EXPECTATIONS.chainId, passed: true },
      { field: 'asset', expected: 'USDC', passed: true },
      { field: 'humanApprovalRequired', expected: true, passed: true },
      { field: 'transactionBroadcast', expected: false, passed: true },
    ],
    transactionBroadcast: false,
  };
}

function combinedObject() {
  return {
    schema: 'arc-mcp-builder-assistant.agentCommerce.flow.v1',
    state,
    flowId: selectedFlowId,
    network: ARC_FLOW_EXPECTATIONS,
    agent: agentObject(),
    request: requestObject(),
    receipt: receiptObject(),
    safety: {
      localOnly: true,
      humanApprovalRequired: true,
      walletConnected: false,
      walletActionEnabled: false,
      signingEnabled: false,
      transactionBroadcast: false,
      backendCalls: false,
      remoteRpcCalls: false,
      liveX402Verification: false,
      mainnetEnabled: false,
    },
    events,
  };
}

function renderFlowNav() {
  nodes.nav.replaceChildren(...Object.entries(FLOW_TEMPLATES).map(([flowId, flow]) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `pill${flowId === selectedFlowId ? ' active' : ''}`;
    button.textContent = flow.title;
    button.addEventListener('click', () => loadFlow(flowId));
    return button;
  }));
}

function render() {
  const flow = activeTemplate();
  nodes.title.textContent = flow.title;
  nodes.description.textContent = flow.description;
  nodes.status.textContent = state;
  nodes.agent.textContent = JSON.stringify(agentObject(), null, 2);
  nodes.request.textContent = JSON.stringify(requestObject(), null, 2);
  nodes.receipt.textContent = JSON.stringify(receiptObject(), null, 2);
  nodes.combined.textContent = JSON.stringify(combinedObject(), null, 2);
  nodes.events.replaceChildren(...events.map((entry) => {
    const li = document.createElement('li');
    li.textContent = `${entry.actor}: ${entry.event} · ${entry.at}`;
    return li;
  }));
  buttons.freeze.disabled = state !== 'draft_review';
  buttons.approve.disabled = state !== 'fields_frozen';
  buttons.receipt.disabled = state !== 'approved_local_no_broadcast';
  renderFlowNav();
}

buttons.freeze.addEventListener('click', () => {
  state = 'fields_frozen';
  frozenAt = nowIso();
  addEvent('Human froze flow money fields before wallet handoff', 'human');
  render();
});
buttons.approve.addEventListener('click', () => {
  state = 'approved_local_no_broadcast';
  approvedAt = nowIso();
  addEvent('Human recorded local approval; no transaction was broadcast', 'human');
  render();
});
buttons.receipt.addEventListener('click', () => {
  state = 'receipt_simulated';
  receiptAt = nowIso();
  addEvent('System generated simulated receipt for the selected flow', 'system');
  render();
});
buttons.reset.addEventListener('click', () => loadFlow(selectedFlowId));
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
  field.addEventListener('change', render);
}
loadFlow(selectedFlowId);

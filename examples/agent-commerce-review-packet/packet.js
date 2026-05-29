const ARC_REVIEW_PACKET = Object.freeze({
  schema: 'arc-mcp-builder-assistant.agentCommerce.reviewPacket.v1',
  network: {
    name: 'arc-testnet',
    chainId: 5042002,
    chainIdHex: '0x4cef52',
  },
});

const fields = {
  agentName: document.querySelector('#agent-name'),
  flowKind: document.querySelector('#flow-kind'),
  amount: document.querySelector('#amount'),
  outcome: document.querySelector('#outcome'),
  approvalNote: document.querySelector('#approval-note'),
};
const nodes = {
  status: document.querySelector('#packet-status'),
  packet: document.querySelector('#packet-json'),
};
const buttons = {
  freeze: document.querySelector('#freeze-packet'),
  reset: document.querySelector('#reset-packet'),
};

let packetState = 'draft_packet';
let frozenAt = null;

function isNoPayoutOutcome(outcome) {
  return ['rejected_no_payout', 'disputed_manual_review', 'expired_no_payout', 'cancelled_no_payout'].includes(outcome);
}

function moneyAmount() {
  const amount = Number(fields.amount.value || 0);
  return Number.isFinite(amount) && amount >= 0 ? amount.toFixed(2) : '0.00';
}

function controls() {
  return {
    localOnly: true,
    walletConnected: false,
    walletActionEnabled: false,
    signingEnabled: false,
    transactionBroadcast: false,
    networkCallsEnabled: false,
    backendCalls: false,
    remoteRpcCalls: false,
    settlementEnabled: false,
    reputationWritten: false,
    validationRequested: false,
    secretRequired: false,
    mainnetEnabled: false,
    humanApprovalRequired: true,
  };
}

function packetObject() {
  const outcome = fields.outcome.value;
  return {
    schema: ARC_REVIEW_PACKET.schema,
    state: packetState,
    status: 'local_review_packet',
    frozenAt,
    network: ARC_REVIEW_PACKET.network,
    agentIdentity: {
      status: 'unregistered_local_preview',
      agentName: fields.agentName.value.trim(),
      registrationTransactionPrepared: false,
    },
    commerceFlow: {
      kind: fields.flowKind.value,
      asset: 'USDC',
      amount: moneyAmount(),
      moneyFieldsFrozen: packetState === 'packet_frozen_for_review',
      sourceExamples: [
        'examples/agent-identity-profile-preview/',
        'examples/agent-commerce-flows/',
        'examples/job-escrow-simulator/',
      ],
    },
    escrowReview: {
      outcome,
      noPayoutOutcome: isNoPayoutOutcome(outcome),
      payoutReleased: false,
      payoutReleaseReason: isNoPayoutOutcome(outcome) ? 'terminal_no_payout_local_state' : 'wallet_and_settlement_disabled',
      approvalNote: fields.approvalNote.value.trim(),
    },
    controls: controls(),
  };
}

function render() {
  nodes.status.textContent = packetState;
  nodes.packet.textContent = JSON.stringify(packetObject(), null, 2);
  buttons.freeze.disabled = packetState === 'packet_frozen_for_review';
}

buttons.freeze.addEventListener('click', () => {
  packetState = 'packet_frozen_for_review';
  frozenAt = new Date().toISOString();
  render();
});
buttons.reset.addEventListener('click', () => {
  packetState = 'draft_packet';
  frozenAt = null;
  fields.agentName.value = 'Research Buyer Agent';
  fields.flowKind.value = 'paid_api_call';
  fields.amount.value = '2.50';
  fields.outcome.value = 'pending_local_review';
  fields.approvalNote.value = 'Reviewer checked money fields, disabled wallet controls, and local-only status.';
  render();
});
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
  field.addEventListener('change', render);
}
render();

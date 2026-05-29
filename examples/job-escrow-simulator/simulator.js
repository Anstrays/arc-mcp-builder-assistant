const stateOrder = ['draft', 'posted', 'accepted_by_agent', 'escrow_funded_simulation', 'work_submitted', 'changes_requested', 'rejected_no_payout', 'disputed_manual_review', 'expired_no_payout', 'cancelled_no_payout', 'payout_approved_simulation'];
const statusLabels = {
  draft: 'Draft job',
  posted: 'Posted for agent review',
  accepted_by_agent: 'Accepted by agent',
  escrow_funded_simulation: 'Escrow funded simulation',
  work_submitted: 'Work submitted for human review',
  changes_requested: 'Changes requested',
  rejected_no_payout: 'Rejected without payout',
  disputed_manual_review: 'Disputed manual review',
  expired_no_payout: 'Expired without payout',
  cancelled_no_payout: 'Cancelled without payout',
  payout_approved_simulation: 'Payout approved simulation',
};
const buttons = {
  post: document.querySelector('#post-job'),
  accept: document.querySelector('#accept-job'),
  fund: document.querySelector('#fund-escrow'),
  submit: document.querySelector('#submit-work'),
  requestChanges: document.querySelector('#request-changes'),
  revise: document.querySelector('#revise-work'),
  reject: document.querySelector('#reject-work'),
  dispute: document.querySelector('#open-dispute'),
  expire: document.querySelector('#expire-job'),
  cancel: document.querySelector('#cancel-job'),
  approve: document.querySelector('#approve-payout'),
  reset: document.querySelector('#reset-flow'),
};
const fields = {
  title: document.querySelector('#job-title'),
  budget: document.querySelector('#budget'),
  agent: document.querySelector('#agent'),
  deliverable: document.querySelector('#deliverable'),
  revisionNote: document.querySelector('#revision-note'),
  disputeNote: document.querySelector('#dispute-note'),
};
const statusPill = document.querySelector('#status-pill');
const jsonPanel = document.querySelector('#escrow-json');
const timeline = document.querySelector('#timeline');
let status = 'draft';
let events = [];
let changesRequestedCount = 0;

function nowIso() {
  return new Date().toISOString();
}

function escrowObject() {
  const budgetValue = Number(fields.budget.value || 0);
  return {
    schema: 'arc-mcp-builder-assistant.jobEscrow.simulation.v1',
    status,
    job: {
      title: fields.title.value.trim(),
      budget: Number.isFinite(budgetValue) ? budgetValue.toFixed(2) : '0.00',
      asset: 'USDC',
      chain: 'Arc Testnet later; local simulation now',
      expectedDeliverable: fields.deliverable.value.trim(),
    },
    parties: {
      requester: 'human_reviewer',
      agent: fields.agent.value.trim(),
      escrow: 'simulated_local_object',
    },
    controls: {
      walletConnected: false,
      walletActionEnabled: false,
      broadcastsTransactions: false,
      transactionBroadcast: false,
      talksToBackend: false,
      signingEnabled: false,
      humanApprovalRequired: true,
      mainnetEnabled: false,
      localOnly: true,
      realEscrowContract: false,
      payoutReleased: status === 'payout_approved_simulation' ? 'simulated_only' : false,
      terminalNoPayoutStates: ['rejected_no_payout', 'disputed_manual_review', 'expired_no_payout', 'cancelled_no_payout'],
      contactsArbitrator: false,
      contactsValidator: false,
      arcTestnetChainId: 5042002,
      arcTestnetChainIdHex: '0x4cef52',
    },
    review: {
      changesRequestedCount,
      latestRevisionNote: fields.revisionNote.value.trim(),
      latestCloseNote: fields.disputeNote.value.trim(),
      terminalStateRequiresNewJob: ['rejected_no_payout', 'disputed_manual_review', 'expired_no_payout', 'cancelled_no_payout'].includes(status),
      payoutRelease: 'simulated_only_after_human_approval',
      agentOutputTrustedOnlyAfterReview: true,
    },
    events,
  };
}

function addEvent(label) {
  events = [...events, { at: nowIso(), label, status }];
}

function setStatus(nextStatus, label) {
  if (nextStatus === 'changes_requested') {
    changesRequestedCount += 1;
  }
  status = nextStatus;
  addEvent(label || statusLabels[nextStatus]);
  render();
}

function render() {
  const currentIndex = stateOrder.indexOf(status);
  statusPill.textContent = statusLabels[status];
  jsonPanel.textContent = JSON.stringify(escrowObject(), null, 2);
  timeline.replaceChildren(...events.map((event) => {
    const li = document.createElement('li');
    li.className = stateOrder.indexOf(event.status) <= currentIndex ? 'done' : '';
    li.textContent = `${event.label} · ${event.at}`;
    return li;
  }));
  buttons.post.disabled = status !== 'draft';
  buttons.accept.disabled = status !== 'posted';
  buttons.fund.disabled = status !== 'accepted_by_agent';
  buttons.submit.disabled = status !== 'escrow_funded_simulation';
  buttons.requestChanges.disabled = status !== 'work_submitted';
  buttons.revise.disabled = status !== 'changes_requested';
  buttons.reject.disabled = status !== 'work_submitted';
  buttons.dispute.disabled = !['work_submitted', 'changes_requested'].includes(status);
  buttons.expire.disabled = !['posted', 'accepted_by_agent', 'escrow_funded_simulation', 'changes_requested'].includes(status);
  buttons.cancel.disabled = !['draft', 'posted', 'accepted_by_agent'].includes(status);
  buttons.approve.disabled = status !== 'work_submitted';
}

function reset() {
  status = 'draft';
  changesRequestedCount = 0;
  fields.disputeNote.value = 'Output missed acceptance criteria; keep funds unreleased in the local simulation.';
  events = [{ at: nowIso(), label: 'Draft created locally', status }];
  render();
}

buttons.post.addEventListener('click', () => setStatus('posted', 'Human posted the job for agent review'));
buttons.accept.addEventListener('click', () => setStatus('accepted_by_agent', 'Agent accepted the job terms'));
buttons.fund.addEventListener('click', () => setStatus('escrow_funded_simulation', 'Human simulated funding escrow'));
buttons.submit.addEventListener('click', () => setStatus('work_submitted', 'Agent submitted the deliverable for review'));
buttons.requestChanges.addEventListener('click', () => setStatus('changes_requested', 'Reviewer requested changes before payout approval'));
buttons.revise.addEventListener('click', () => setStatus('work_submitted', 'Agent resubmitted revised work for review'));
buttons.reject.addEventListener('click', () => setStatus('rejected_no_payout', 'Reviewer rejected the work; no payout released'));
buttons.dispute.addEventListener('click', () => setStatus('disputed_manual_review', 'Reviewer opened a manual dispute; no payout released'));
buttons.expire.addEventListener('click', () => setStatus('expired_no_payout', 'Job expired locally; no payout released'));
buttons.cancel.addEventListener('click', () => setStatus('cancelled_no_payout', 'Human cancelled the job locally; no payout released'));
buttons.approve.addEventListener('click', () => setStatus('payout_approved_simulation', 'Human approved simulated payout release'));
buttons.reset.addEventListener('click', reset);
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
}
reset();

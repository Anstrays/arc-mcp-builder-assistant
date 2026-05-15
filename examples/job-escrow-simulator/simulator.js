const stateOrder = ['draft', 'posted', 'accepted_by_agent', 'escrow_funded_simulation', 'work_submitted', 'payout_approved_simulation'];
const statusLabels = {
  draft: 'Draft job',
  posted: 'Posted for agent review',
  accepted_by_agent: 'Accepted by agent',
  escrow_funded_simulation: 'Escrow funded simulation',
  work_submitted: 'Work submitted for human review',
  payout_approved_simulation: 'Payout approved simulation',
};
const buttons = {
  post: document.querySelector('#post-job'),
  accept: document.querySelector('#accept-job'),
  fund: document.querySelector('#fund-escrow'),
  submit: document.querySelector('#submit-work'),
  approve: document.querySelector('#approve-payout'),
  reset: document.querySelector('#reset-flow'),
};
const fields = {
  title: document.querySelector('#job-title'),
  budget: document.querySelector('#budget'),
  agent: document.querySelector('#agent'),
  deliverable: document.querySelector('#deliverable'),
};
const statusPill = document.querySelector('#status-pill');
const jsonPanel = document.querySelector('#escrow-json');
const timeline = document.querySelector('#timeline');
let status = 'draft';
let events = [];

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
      broadcastsTransactions: false,
      talksToBackend: false,
      humanApprovalRequired: true,
      mainnetEnabled: false,
    },
    events,
  };
}

function addEvent(label) {
  events = [...events, { at: nowIso(), label, status }];
}

function setStatus(nextStatus, label) {
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
  buttons.approve.disabled = status !== 'work_submitted';
}

function reset() {
  status = 'draft';
  events = [{ at: nowIso(), label: 'Draft created locally', status }];
  render();
}

buttons.post.addEventListener('click', () => setStatus('posted', 'Human posted the job for agent review'));
buttons.accept.addEventListener('click', () => setStatus('accepted_by_agent', 'Agent accepted the job terms'));
buttons.fund.addEventListener('click', () => setStatus('escrow_funded_simulation', 'Human simulated funding escrow'));
buttons.submit.addEventListener('click', () => setStatus('work_submitted', 'Agent submitted the deliverable for review'));
buttons.approve.addEventListener('click', () => setStatus('payout_approved_simulation', 'Human approved simulated payout release'));
buttons.reset.addEventListener('click', reset);
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
}
reset();

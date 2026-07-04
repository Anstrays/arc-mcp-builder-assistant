import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = fs.readFileSync(
  path.join(root, 'examples', 'arc-agent-treasury-lab', 'treasury.js'),
  'utf8',
);
const context = vm.createContext({
  console,
  structuredClone,
  setTimeout,
  clearTimeout,
});
vm.runInContext(source, context, { filename: 'treasury.js' });
const domain = context.ArcAgentTreasuryDomain;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function defaultTask(overrides = {}) {
  return {
    requestId: 'req-1',
    receiptId: 'receipt-1',
    service: 'Arc documentation research report',
    quotedRevenue: '1.00',
    computeCostPerAttempt: '0.15',
    maxAttempts: 3,
    scenario: 'fail_then_pass',
    ...overrides,
  };
}

assert(domain.parseUsdc('1.000001') === 1000001, 'USDC parsing must use exact micro-units');
assert(domain.formatUsdc(1000001) === '1.000001', 'USDC formatting must preserve micro-units');
let invalidPrecisionRejected = false;
try {
  domain.parseUsdc('0.0000001');
} catch {
  invalidPrecisionRejected = true;
}
assert(invalidPrecisionRejected, 'over-precision USDC must fail closed');

let state = domain.createState();
state = domain.reviewPaidTask(state, defaultTask());
assert(state.lastDecision.approved === true, 'profitable task should be approved');
assert(state.treasury.balanceMicro === 6000000, 'accepted local receipt should credit quoted revenue once');
assert(state.controls.mainnetEnabled === false, 'mainnet must remain disabled');
assert(state.controls.transactionBroadcast === false, 'transaction broadcast must remain disabled');
assert(state.controls.autonomousSpendingEnabled === false, 'live autonomous spending must remain disabled');

state = domain.runVerifiedLoop(state);
assert(state.status === 'completed', 'repair-then-pass task should complete');
assert(state.currentTask.attempts.length === 2, 'repair-then-pass task should use exactly two attempts');
assert(state.currentTask.outputVerified === true, 'completed task must be explicitly verified');
assert(state.treasury.spentMicro === 300000, 'actual compute spend must match attempts');
assert(state.treasury.balanceMicro === 5700000, 'balance must equal opening plus revenue minus actual compute');

state = domain.clearFinishedTask(state);
state = domain.reviewPaidTask(state, defaultTask());
assert(state.lastDecision.approved === false, 'replayed request and receipt must be denied');
assert(state.lastDecision.reasons.includes('request_replay_detected'), 'request replay reason missing');
assert(state.lastDecision.reasons.includes('receipt_replay_detected'), 'receipt replay reason missing');
assert(state.treasury.earnedMicro === 1000000, 'replay must not credit revenue twice');

let capState = domain.createState();
capState = domain.reviewPaidTask(capState, defaultTask({
  requestId: 'req-cap',
  receiptId: 'receipt-cap',
  computeCostPerAttempt: '0.60',
  maxAttempts: 3,
}));
assert(capState.lastDecision.reasons.includes('single_task_cap_exceeded'), 'single-task cap must fail closed');

let marginState = domain.createState();
marginState = domain.reviewPaidTask(marginState, defaultTask({
  requestId: 'req-margin',
  receiptId: 'receipt-margin',
  quotedRevenue: '0.40',
  computeCostPerAttempt: '0.15',
  maxAttempts: 3,
}));
assert(marginState.lastDecision.reasons.includes('minimum_profit_not_met'), 'minimum-profit policy must fail closed');

let reserveState = domain.createState({ openingBalance: '2', reserve: '2' });
reserveState = domain.reviewPaidTask(reserveState, defaultTask({
  requestId: 'req-reserve',
  receiptId: 'receipt-reserve',
  quotedRevenue: '0.10',
  computeCostPerAttempt: '0.20',
  maxAttempts: 1,
}));
assert(reserveState.lastDecision.reasons.includes('protected_reserve_would_be_breached'), 'reserve breach must fail closed');

let exhaustState = domain.createState();
exhaustState = domain.reviewPaidTask(exhaustState, defaultTask({
  requestId: 'req-exhaust',
  receiptId: 'receipt-exhaust',
  scenario: 'exhaust_retries',
}));
exhaustState = domain.runVerifiedLoop(exhaustState);
assert(exhaustState.status === 'failed_manual_review', 'exhausted verification must require manual review');
assert(exhaustState.currentTask.outputVerified === false, 'failed task must not claim verified output');
assert(exhaustState.currentTask.manualRefundReviewRequired === true, 'failed paid task must flag refund review');

let runtimeState = domain.createState();
runtimeState = domain.reviewPaidTask(runtimeState, defaultTask({
  requestId: 'req-runtime',
  receiptId: 'receipt-runtime',
  scenario: 'pass_first',
}));
runtimeState.policy.dailySpendCapMicro = 0;
runtimeState = domain.runVerifiedLoop(runtimeState);
assert(runtimeState.status === 'policy_blocked', 'runtime policy drift must fail closed before spend');
assert(runtimeState.treasury.spentMicro === 0, 'runtime policy block must happen before spend');

const snapshot = domain.publicSnapshot(exhaustState);
assert(snapshot.treasury.balance === '5.55', 'public snapshot balance mismatch');
assert(snapshot.receipts[0].settled === false, 'local receipt must never claim settlement');
assert(snapshot.receipts[0].transactionBroadcast === false, 'local receipt must never claim broadcast');

console.log('arc agent treasury behavior harness passed: exact micro-USDC, policy caps, replay, verified loop, runtime fail-closed');

const ARC_AGENT_TREASURY = (() => {
  'use strict';

  const MICRO_USDC = 1_000_000;
  const MAX_SAFE_USDC = 1_000_000;
  const SCENARIOS = Object.freeze({
    pass_first: ['passed'],
    fail_then_pass: ['failed', 'passed'],
    exhaust_retries: ['failed', 'failed', 'failed', 'failed', 'failed'],
  });

  function parseUsdc(value, label = 'amount') {
    const text = String(value ?? '').trim();
    if (!/^(?:0|[1-9]\d*)(?:\.\d{1,6})?$/.test(text)) {
      throw new Error(`${label} must be a non-negative USDC decimal with at most 6 places.`);
    }
    const [whole, fraction = ''] = text.split('.');
    const micro = (Number(whole) * MICRO_USDC) + Number(fraction.padEnd(6, '0'));
    if (!Number.isSafeInteger(micro) || micro > MAX_SAFE_USDC * MICRO_USDC) {
      throw new Error(`${label} exceeds the local simulation limit.`);
    }
    return micro;
  }

  function formatUsdc(micro) {
    if (!Number.isSafeInteger(micro)) {
      throw new Error('USDC micro-unit value must be a safe integer.');
    }
    const sign = micro < 0 ? '-' : '';
    const absolute = Math.abs(micro);
    const whole = Math.floor(absolute / MICRO_USDC);
    const fraction = String(absolute % MICRO_USDC).padStart(6, '0').replace(/0+$/, '');
    return `${sign}${whole}${fraction ? `.${fraction}` : ''}`;
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function requireIdentifier(value, label) {
    const text = String(value ?? '').trim();
    if (!/^[A-Za-z0-9._-]{3,64}$/.test(text)) {
      throw new Error(`${label} must use 3-64 letters, numbers, dots, underscores, or hyphens.`);
    }
    return text;
  }

  function normalizePolicy(input = {}) {
    const policy = {
      openingBalanceMicro: parseUsdc(input.openingBalance ?? '5', 'opening balance'),
      reserveMicro: parseUsdc(input.reserve ?? '2', 'reserve'),
      dailySpendCapMicro: parseUsdc(input.dailySpendCap ?? '2', 'daily spend cap'),
      singleTaskCapMicro: parseUsdc(input.singleTaskCap ?? '1', 'single-task cap'),
      minProfitMicro: parseUsdc(input.minProfit ?? '0.10', 'minimum profit'),
      maxAttempts: Number(input.maxAttempts ?? 5),
    };
    if (!Number.isInteger(policy.maxAttempts) || policy.maxAttempts < 1 || policy.maxAttempts > 5) {
      throw new Error('policy max attempts must be an integer from 1 to 5.');
    }
    if (policy.openingBalanceMicro < policy.reserveMicro) {
      throw new Error('opening balance must be at least the protected reserve.');
    }
    if (policy.dailySpendCapMicro <= 0 || policy.singleTaskCapMicro <= 0) {
      throw new Error('spend caps must be greater than zero.');
    }
    return policy;
  }

  function safetyControls() {
    return {
      network: 'arc-testnet',
      chainId: 5042002,
      chainIdHex: '0x4cef52',
      asset: 'USDC',
      assetDecimals: 6,
      localOnly: true,
      simulatedX402ReceiptsOnly: true,
      walletConnected: false,
      signingEnabled: false,
      custodyEnabled: false,
      mainnetEnabled: false,
      autonomousSpendingEnabled: false,
      transactionBroadcast: false,
      talksToBackend: false,
      humanApprovalRequiredForLiveExtension: true,
    };
  }

  function createState(policyInput = {}) {
    const policy = normalizePolicy(policyInput);
    return {
      schema: 'arc-mcp-builder-assistant.agentTreasury.local.v1',
      status: 'ready',
      policy,
      treasury: {
        balanceMicro: policy.openingBalanceMicro,
        earnedMicro: 0,
        spentMicro: 0,
        dailySpendMicro: 0,
      },
      counters: {
        accepted: 0,
        denied: 0,
        completed: 0,
        failed: 0,
      },
      processedRequestIds: [],
      acceptedReceiptIds: [],
      receipts: [],
      events: [{
        at: nowIso(),
        type: 'lab_reset',
        message: 'Local Arc Agent Treasury policy initialized.',
      }],
      currentTask: null,
      lastDecision: null,
      controls: safetyControls(),
    };
  }

  function normalizeTask(input, policy) {
    const task = {
      requestId: requireIdentifier(input.requestId, 'request ID'),
      receiptId: requireIdentifier(input.receiptId, 'receipt ID'),
      service: String(input.service ?? '').trim(),
      quotedRevenueMicro: parseUsdc(input.quotedRevenue, 'quoted revenue'),
      computeCostPerAttemptMicro: parseUsdc(input.computeCostPerAttempt, 'compute cost per attempt'),
      maxAttempts: Number(input.maxAttempts),
      scenario: String(input.scenario ?? ''),
    };
    if (!task.service || task.service.length > 120) {
      throw new Error('service must contain 1-120 characters.');
    }
    if (task.quotedRevenueMicro <= 0 || task.computeCostPerAttemptMicro <= 0) {
      throw new Error('quoted revenue and compute cost must be greater than zero.');
    }
    if (!Number.isInteger(task.maxAttempts) || task.maxAttempts < 1 || task.maxAttempts > policy.maxAttempts) {
      throw new Error(`task max attempts must be an integer from 1 to ${policy.maxAttempts}.`);
    }
    if (!Object.hasOwn(SCENARIOS, task.scenario)) {
      throw new Error('scenario is not supported.');
    }
    task.worstCaseCostMicro = task.computeCostPerAttemptMicro * task.maxAttempts;
    task.expectedProfitMicro = task.quotedRevenueMicro - task.worstCaseCostMicro;
    return task;
  }

  function decisionFor(state, task) {
    const reasons = [];
    const projectedBalanceMicro = state.treasury.balanceMicro
      + task.quotedRevenueMicro
      - task.worstCaseCostMicro;
    const projectedDailySpendMicro = state.treasury.dailySpendMicro + task.worstCaseCostMicro;

    if (state.processedRequestIds.includes(task.requestId)) reasons.push('request_replay_detected');
    if (state.acceptedReceiptIds.includes(task.receiptId)) reasons.push('receipt_replay_detected');
    if (task.worstCaseCostMicro > state.policy.singleTaskCapMicro) reasons.push('single_task_cap_exceeded');
    if (projectedDailySpendMicro > state.policy.dailySpendCapMicro) reasons.push('daily_spend_cap_exceeded');
    if (projectedBalanceMicro < state.policy.reserveMicro) reasons.push('protected_reserve_would_be_breached');
    if (task.expectedProfitMicro < state.policy.minProfitMicro) reasons.push('minimum_profit_not_met');

    return {
      approved: reasons.length === 0,
      reasons,
      requestId: task.requestId,
      receiptId: task.receiptId,
      quotedRevenueMicro: task.quotedRevenueMicro,
      worstCaseCostMicro: task.worstCaseCostMicro,
      expectedProfitMicro: task.expectedProfitMicro,
      projectedBalanceMicro,
      projectedDailySpendMicro,
    };
  }

  function reviewPaidTask(currentState, input) {
    const state = clone(currentState);
    if (state.currentTask && state.currentTask.status === 'reviewed') {
      throw new Error('finish or clear the reviewed task before reviewing another.');
    }
    let task;
    try {
      task = normalizeTask(input, state.policy);
    } catch (error) {
      state.counters.denied += 1;
      state.status = 'denied';
      state.lastDecision = { approved: false, reasons: ['invalid_task'], detail: error.message };
      state.events.push({ at: nowIso(), type: 'task_denied', message: error.message });
      return state;
    }
    const decision = decisionFor(state, task);
    state.lastDecision = decision;
    if (!decision.approved) {
      state.counters.denied += 1;
      state.status = 'denied';
      state.events.push({
        at: nowIso(),
        type: 'task_denied',
        requestId: task.requestId,
        message: `Policy denied task: ${decision.reasons.join(', ')}.`,
      });
      return state;
    }

    state.treasury.balanceMicro += task.quotedRevenueMicro;
    state.treasury.earnedMicro += task.quotedRevenueMicro;
    state.processedRequestIds.push(task.requestId);
    state.acceptedReceiptIds.push(task.receiptId);
    state.receipts.push({
      receiptId: task.receiptId,
      requestId: task.requestId,
      amountMicro: task.quotedRevenueMicro,
      asset: 'USDC',
      network: 'arc-testnet',
      verifierMode: 'local-simulation',
      settled: false,
      transactionBroadcast: false,
    });
    state.currentTask = {
      ...task,
      status: 'reviewed',
      attempts: [],
      actualCostMicro: 0,
      actualProfitMicro: 0,
      outputVerified: false,
      manualRefundReviewRequired: false,
    };
    state.counters.accepted += 1;
    state.status = 'reviewed';
    state.events.push({
      at: nowIso(),
      type: 'task_reviewed',
      requestId: task.requestId,
      message: 'Local x402 receipt accepted and worst-case compute budget reserved by policy.',
    });
    return state;
  }

  function canSpendAttempt(state, task) {
    return task.actualCostMicro + task.computeCostPerAttemptMicro <= task.worstCaseCostMicro
      && state.treasury.dailySpendMicro + task.computeCostPerAttemptMicro <= state.policy.dailySpendCapMicro
      && state.treasury.balanceMicro - task.computeCostPerAttemptMicro >= state.policy.reserveMicro;
  }

  function runVerifiedLoop(currentState) {
    const state = clone(currentState);
    const task = state.currentTask;
    if (!task || task.status !== 'reviewed') {
      throw new Error('a policy-approved reviewed task is required before running the loop.');
    }
    const outcomes = SCENARIOS[task.scenario];
    task.status = 'running';
    state.status = 'running';

    for (let index = 0; index < task.maxAttempts; index += 1) {
      if (!canSpendAttempt(state, task)) {
        task.status = 'policy_blocked';
        state.status = 'policy_blocked';
        task.manualRefundReviewRequired = true;
        state.counters.failed += 1;
        state.events.push({
          at: nowIso(),
          type: 'loop_blocked',
          requestId: task.requestId,
          message: 'Runtime spend preflight failed closed before the next compute attempt.',
        });
        return state;
      }
      state.treasury.balanceMicro -= task.computeCostPerAttemptMicro;
      state.treasury.spentMicro += task.computeCostPerAttemptMicro;
      state.treasury.dailySpendMicro += task.computeCostPerAttemptMicro;
      task.actualCostMicro += task.computeCostPerAttemptMicro;
      const verification = outcomes[Math.min(index, outcomes.length - 1)];
      const attempt = {
        attempt: index + 1,
        stages: ['reproduce', 'execute', 'verify'],
        verification,
        costMicro: task.computeCostPerAttemptMicro,
      };
      if (verification === 'failed' && index + 1 < task.maxAttempts) {
        attempt.stages.push('repair');
      }
      task.attempts.push(attempt);
      state.events.push({
        at: nowIso(),
        type: verification === 'passed' ? 'verification_passed' : 'verification_failed',
        requestId: task.requestId,
        message: `Attempt ${index + 1} verification ${verification}.`,
      });
      if (verification === 'passed') {
        task.status = 'completed';
        task.outputVerified = true;
        task.actualProfitMicro = task.quotedRevenueMicro - task.actualCostMicro;
        state.status = 'completed';
        state.counters.completed += 1;
        return state;
      }
    }
    task.status = 'failed_manual_review';
    task.actualProfitMicro = task.quotedRevenueMicro - task.actualCostMicro;
    task.manualRefundReviewRequired = true;
    state.status = 'failed_manual_review';
    state.counters.failed += 1;
    state.events.push({
      at: nowIso(),
      type: 'manual_review_required',
      requestId: task.requestId,
      message: 'Verification attempts exhausted; no success claim emitted.',
    });
    return state;
  }

  function clearFinishedTask(currentState) {
    const state = clone(currentState);
    if (state.currentTask && ['reviewed', 'running'].includes(state.currentTask.status)) {
      throw new Error('cannot clear an active reviewed task.');
    }
    state.currentTask = null;
    state.status = 'ready';
    state.lastDecision = null;
    state.events.push({ at: nowIso(), type: 'next_task_ready', message: 'Treasury ready for another request.' });
    return state;
  }

  function publicSnapshot(state) {
    const snapshot = clone(state);
    snapshot.treasury = {
      balance: formatUsdc(state.treasury.balanceMicro),
      earned: formatUsdc(state.treasury.earnedMicro),
      spent: formatUsdc(state.treasury.spentMicro),
      dailySpend: formatUsdc(state.treasury.dailySpendMicro),
      netChange: formatUsdc(state.treasury.earnedMicro - state.treasury.spentMicro),
    };
    snapshot.policy = {
      reserve: formatUsdc(state.policy.reserveMicro),
      dailySpendCap: formatUsdc(state.policy.dailySpendCapMicro),
      singleTaskCap: formatUsdc(state.policy.singleTaskCapMicro),
      minProfit: formatUsdc(state.policy.minProfitMicro),
      maxAttempts: state.policy.maxAttempts,
    };
    delete snapshot.policy.openingBalanceMicro;
    if (snapshot.currentTask) {
      for (const key of [
        'quotedRevenueMicro',
        'computeCostPerAttemptMicro',
        'worstCaseCostMicro',
        'expectedProfitMicro',
        'actualCostMicro',
        'actualProfitMicro',
      ]) {
        snapshot.currentTask[key.replace('Micro', '')] = formatUsdc(snapshot.currentTask[key]);
        delete snapshot.currentTask[key];
      }
      for (const attempt of snapshot.currentTask.attempts) {
        attempt.cost = formatUsdc(attempt.costMicro);
        delete attempt.costMicro;
      }
    }
    snapshot.receipts = snapshot.receipts.map((receipt) => {
      const { amountMicro, ...publicReceipt } = receipt;
      return { ...publicReceipt, amount: formatUsdc(amountMicro) };
    });
    return snapshot;
  }

  return Object.freeze({
    MICRO_USDC,
    SCENARIOS,
    parseUsdc,
    formatUsdc,
    createState,
    reviewPaidTask,
    runVerifiedLoop,
    clearFinishedTask,
    publicSnapshot,
  });
})();

globalThis.ArcAgentTreasuryDomain = ARC_AGENT_TREASURY;

if (typeof document !== 'undefined') {
  const elements = {
    openingBalance: document.querySelector('#opening-balance'),
    reserve: document.querySelector('#reserve'),
    dailyCap: document.querySelector('#daily-cap'),
    singleTaskCap: document.querySelector('#single-task-cap'),
    minProfit: document.querySelector('#min-profit'),
    policyAttempts: document.querySelector('#policy-attempts'),
    requestId: document.querySelector('#request-id'),
    receiptId: document.querySelector('#receipt-id'),
    service: document.querySelector('#service'),
    revenue: document.querySelector('#quoted-revenue'),
    computeCost: document.querySelector('#compute-cost'),
    taskAttempts: document.querySelector('#task-attempts'),
    scenario: document.querySelector('#scenario'),
    review: document.querySelector('#review-task'),
    run: document.querySelector('#run-loop'),
    next: document.querySelector('#next-task'),
    reset: document.querySelector('#reset-lab'),
    status: document.querySelector('#status'),
    balance: document.querySelector('#metric-balance'),
    earned: document.querySelector('#metric-earned'),
    spent: document.querySelector('#metric-spent'),
    net: document.querySelector('#metric-net'),
    decision: document.querySelector('#decision'),
    ledger: document.querySelector('#ledger'),
    snapshot: document.querySelector('#snapshot'),
  };
  let state;

  function policyInput() {
    return {
      openingBalance: elements.openingBalance.value,
      reserve: elements.reserve.value,
      dailySpendCap: elements.dailyCap.value,
      singleTaskCap: elements.singleTaskCap.value,
      minProfit: elements.minProfit.value,
      maxAttempts: elements.policyAttempts.value,
    };
  }

  function taskInput() {
    return {
      requestId: elements.requestId.value,
      receiptId: elements.receiptId.value,
      service: elements.service.value,
      quotedRevenue: elements.revenue.value,
      computeCostPerAttempt: elements.computeCost.value,
      maxAttempts: elements.taskAttempts.value,
      scenario: elements.scenario.value,
    };
  }

  function setError(error) {
    elements.decision.textContent = error.message;
    elements.decision.dataset.verdict = 'error';
  }

  function render() {
    const snapshot = ARC_AGENT_TREASURY.publicSnapshot(state);
    elements.status.textContent = state.status.replaceAll('_', ' ');
    elements.status.dataset.state = state.status;
    elements.balance.textContent = `${snapshot.treasury.balance} USDC`;
    elements.earned.textContent = `${snapshot.treasury.earned} USDC`;
    elements.spent.textContent = `${snapshot.treasury.spent} USDC`;
    elements.net.textContent = `${snapshot.treasury.netChange} USDC`;
    elements.snapshot.textContent = JSON.stringify(snapshot, null, 2);
    elements.decision.textContent = state.lastDecision
      ? state.lastDecision.approved
        ? `APPROVED · worst-case cost ${ARC_AGENT_TREASURY.formatUsdc(state.lastDecision.worstCaseCostMicro)} USDC`
        : `DENIED · ${state.lastDecision.reasons.join(', ')}`
      : 'No task reviewed yet.';
    elements.decision.dataset.verdict = state.lastDecision?.approved ? 'approved' : state.lastDecision ? 'denied' : 'idle';
    elements.ledger.replaceChildren(...state.events.slice().reverse().map((event) => {
      const row = document.createElement('li');
      const strong = document.createElement('strong');
      const span = document.createElement('span');
      strong.textContent = event.type.replaceAll('_', ' ');
      span.textContent = event.message;
      row.append(strong, span);
      return row;
    }));

    const active = state.currentTask && ['reviewed', 'running'].includes(state.currentTask.status);
    const finished = state.currentTask && !active;
    const policyFrozen = state.counters.accepted > 0 || state.counters.denied > 0;
    for (const input of [
      elements.openingBalance,
      elements.reserve,
      elements.dailyCap,
      elements.singleTaskCap,
      elements.minProfit,
      elements.policyAttempts,
    ]) input.disabled = policyFrozen;
    for (const input of [
      elements.requestId,
      elements.receiptId,
      elements.service,
      elements.revenue,
      elements.computeCost,
      elements.taskAttempts,
      elements.scenario,
    ]) input.disabled = active;
    elements.review.disabled = Boolean(active);
    elements.run.disabled = !state.currentTask || state.currentTask.status !== 'reviewed';
    elements.next.disabled = !finished;
  }

  function reset() {
    try {
      state = ARC_AGENT_TREASURY.createState(policyInput());
      render();
    } catch (error) {
      setError(error);
    }
  }

  elements.review.addEventListener('click', () => {
    try {
      if (state.counters.accepted === 0 && state.counters.denied === 0) {
        state = ARC_AGENT_TREASURY.createState(policyInput());
      }
      state = ARC_AGENT_TREASURY.reviewPaidTask(state, taskInput());
      render();
    } catch (error) {
      setError(error);
    }
  });
  elements.run.addEventListener('click', () => {
    try {
      state = ARC_AGENT_TREASURY.runVerifiedLoop(state);
      render();
    } catch (error) {
      setError(error);
    }
  });
  elements.next.addEventListener('click', () => {
    try {
      state = ARC_AGENT_TREASURY.clearFinishedTask(state);
      elements.requestId.value = `req-${state.processedRequestIds.length + 1}`;
      elements.receiptId.value = `receipt-${state.acceptedReceiptIds.length + 1}`;
      render();
    } catch (error) {
      setError(error);
    }
  });
  elements.reset.addEventListener('click', reset);
  reset();
}

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
const finalConfirmationCheckbox = document.querySelector('#final-confirmation-checkbox');
const finalConfirmationButton = document.querySelector('#final-confirmation-button');
const finalConfirmationReasons = document.querySelector('#final-confirmation-reasons');
const unsignedTransactionDraft = document.querySelector('#unsigned-transaction-draft');
const draftConsistencyList = document.querySelector('#draft-consistency-list');
const walletHandoffReadinessList = document.querySelector('#wallet-handoff-readiness-list');
const walletHandoffReadinessJson = document.querySelector('#wallet-handoff-readiness-json');

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
    id: 'final_review_confirmed',
    label: 'Final review confirmed',
    description: 'Final local confirmation is recorded without a wallet request.',
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
let finalConfirmationRecorded = false;

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

function toPaddedHexFromDecimalString(decimalString) {
  if (!/^(?:0|[1-9]\d*)$/.test(decimalString)) return null;
  return BigInt(decimalString).toString(16).padStart(64, '0');
}

function buildErc20TransferCalldata(intent) {
  if (!hasValidRecipient(intent.recipient) || !hasValidUsdcAmount(intent.amount)) return null;
  const baseUnits = formatUsdcBaseUnits(intent.amount);
  const paddedRecipient = intent.recipient.toLowerCase().replace(/^0x/, '').padStart(64, '0');
  const paddedAmount = toPaddedHexFromDecimalString(baseUnits);
  if (!paddedAmount) return null;
  return `0xa9059cbb${paddedRecipient}${paddedAmount}`;
}

function buildUnsignedTransactionDraft(intent) {
  const baseUnits = formatUsdcBaseUnits(intent.amount);
  const isSupportedAsset = intent.asset === 'USDC';
  const calldata = isSupportedAsset ? buildErc20TransferCalldata(intent) : null;
  const readyForDraft = Boolean(calldata) && hasFutureExpiry(intent.expiry);

  return {
    type: 'unsigned_erc20_transfer_preview',
    status: readyForDraft ? 'draft_ready_for_review' : 'blocked',
    localOnly: true,
    unsignedOnly: true,
    walletRequestEnabled: false,
    gasEstimateIncluded: false,
    simulationIncluded: false,
    chainId: ARC_TESTNET_STATUS.expectedChainIdDecimal,
    chainIdHex: ARC_TESTNET_STATUS.expectedChainIdHex,
    to: ARC_TESTNET_STATUS.erc20UsdcAddress,
    value: '0x0',
    data: calldata,
    decoded: {
      method: 'transfer(address,uint256)',
      recipient: hasValidRecipient(intent.recipient) ? intent.recipient : null,
      amountDecimal: hasValidUsdcAmount(intent.amount) ? intent.amount : null,
      amountBaseUnits: baseUnits === 'invalid' ? null : baseUnits,
      asset: intent.asset,
      assetSupported: isSupportedAsset,
      assetDecimals: ARC_TESTNET_STATUS.erc20UsdcDecimals,
    },
    blockers: [
      ...(!isSupportedAsset ? ['Only USDC is supported for the first transaction draft.'] : []),
      ...(!hasValidRecipient(intent.recipient) ? ['Recipient is not a 0x-prefixed 40-byte address.'] : []),
      ...(!hasValidUsdcAmount(intent.amount) ? ['Amount must be positive with at most 6 decimals.'] : []),
      ...(!hasFutureExpiry(intent.expiry) ? ['Expiry must be in the future.'] : []),
      'Draft is not a wallet request and cannot move funds.',
    ],
  };
}

function decodeErc20TransferCalldata(data) {
  if (typeof data !== 'string' || !/^0xa9059cbb[0-9a-fA-F]{128}$/.test(data)) return null;
  const recipientWord = data.slice(10, 74);
  const amountWord = data.slice(74, 138);
  const recipient = `0x${recipientWord.slice(24)}`.toLowerCase();
  const amountBaseUnits = BigInt(`0x${amountWord}`).toString(10);
  return {
    method: 'transfer(address,uint256)',
    recipient,
    amountBaseUnits,
  };
}

function buildTransactionDraftConsistencyCheck(intent) {
  const draft = buildUnsignedTransactionDraft(intent);
  const decodedCalldata = decodeErc20TransferCalldata(draft.data);
  const expectedBaseUnits = formatUsdcBaseUnits(intent.amount);
  const expectedRecipient = hasValidRecipient(intent.recipient) ? intent.recipient.toLowerCase() : null;
  const checks = [
    {
      id: 'unsigned-only',
      label: 'Unsigned-only guard',
      passed: draft.unsignedOnly === true && draft.walletRequestEnabled === false,
      detail: 'Draft cannot open a wallet request by itself.',
    },
    {
      id: 'token-target',
      label: 'Token target',
      passed: draft.to === ARC_TESTNET_STATUS.erc20UsdcAddress,
      detail: 'Transaction target remains the reviewed Arc Testnet USDC token address.',
    },
    {
      id: 'native-value',
      label: 'Native value',
      passed: draft.value === '0x0',
      detail: 'ERC-20 transfer uses zero native value.',
    },
    {
      id: 'chain-id',
      label: 'Arc Testnet chain',
      passed: draft.chainId === ARC_TESTNET_STATUS.expectedChainIdDecimal && draft.chainIdHex === ARC_TESTNET_STATUS.expectedChainIdHex,
      detail: 'Draft chain ID stays pinned to Arc Testnet constants.',
    },
    {
      id: 'calldata-decodes',
      label: 'Calldata decodes',
      passed: Boolean(decodedCalldata),
      detail: 'Data must decode as ERC-20 transfer(address,uint256).',
    },
    {
      id: 'recipient-match',
      label: 'Recipient match',
      passed: Boolean(decodedCalldata) && decodedCalldata.recipient === expectedRecipient,
      detail: 'Decoded calldata recipient must match the current intent recipient.',
    },
    {
      id: 'amount-match',
      label: 'Amount match',
      passed: Boolean(decodedCalldata) && expectedBaseUnits !== 'invalid' && decodedCalldata.amountBaseUnits === expectedBaseUnits,
      detail: 'Decoded calldata amount must match the 6-decimal USDC base units.',
    },
  ];

  return {
    type: 'local_unsigned_transaction_consistency_check',
    localOnly: true,
    walletRequestEnabled: false,
    decodedCalldata,
    allPassed: checks.every((check) => check.passed),
    checks,
  };
}

function renderUnitPreview(intent) {
  const preview = buildUnitPreview(intent);
  erc20BaseUnits.textContent = preview.baseUnits;
  erc20Decimals.textContent = String(preview.erc20Decimals);
  nativeGasDecimals.textContent = String(preview.nativeGasDecimals);
}

function renderUnsignedTransactionDraft(intent) {
  unsignedTransactionDraft.textContent = JSON.stringify(buildUnsignedTransactionDraft(intent), null, 2);
}

function renderTransactionDraftConsistencyCheck(intent) {
  const consistencyCheck = buildTransactionDraftConsistencyCheck(intent);
  draftConsistencyList.replaceChildren(
    ...consistencyCheck.checks.map((check) => {
      const item = document.createElement('li');
      const strong = document.createElement('strong');
      strong.textContent = `${check.passed ? 'PASS' : 'BLOCK'} · ${check.label}`;
      item.append(strong, document.createTextNode(` — ${check.detail}`));
      return item;
    })
  );
}

function buildWalletHandoffReadinessManifest(intent) {
  const validationSummary = buildValidationSummary(intent);
  const transactionDraftConsistency = buildTransactionDraftConsistencyCheck(intent);
  const walletPreview = getWalletPreviewState(intent);
  const frozenIntentPassed = Boolean(frozenIntentSnapshot) && !hasFrozenIntentChanged(intent);
  const humanApprovalPassed = hasHumanApprovalMarker();
  const checks = [
    {
      id: 'valid-intent-fields',
      label: 'Intent fields are locally valid',
      passed: validationSummary.every((check) => check.passed),
      detail: 'Recipient, amount, expiry, and local approval prerequisites must be reviewable.',
    },
    {
      id: 'frozen-intent-present',
      label: 'Frozen intent snapshot is unchanged',
      passed: frozenIntentPassed,
      detail: 'Future wallet request must be generated from the same frozen fields reviewers saw.',
    },
    {
      id: 'human-approval-recorded',
      label: 'Human approval marker is present',
      passed: humanApprovalPassed,
      detail: 'Local approval is required but still is not wallet consent.',
    },
    {
      id: 'final-confirmation-recorded',
      label: 'Final local confirmation is recorded',
      passed: finalConfirmationRecorded,
      detail: 'A future send PR must require a fresh final review before opening a wallet prompt.',
    },
    {
      id: 'unsigned-draft-consistent',
      label: 'Unsigned transaction draft is consistent',
      passed: transactionDraftConsistency.allPassed,
      detail: 'Calldata, token target, chain, and native value must match the reviewed intent.',
    },
    {
      id: 'wallet-chain-observed',
      label: 'Wallet chain observed as Arc Testnet',
      passed: walletPreview.chainMatches,
      detail: 'This playground does not request accounts or switch chains; a future wallet PR must prove this live.',
    },
    {
      id: 'wallet-request-still-disabled',
      label: 'Wallet request remains disabled here',
      passed: walletPreview.walletActionEnabled === false,
      detail: 'This manifest cannot enable wallet send calls, signing, simulation, or broadcast.'
    },
  ];

  return {
    type: 'wallet_handoff_readiness_manifest',
    localOnly: true,
    walletRequestEnabled: false,
    canRequestWallet: false,
    sendPrRequired: true,
    requiredBeforeSend: checks.map((check) => check.id),
    allLocalPrerequisitesPassed: checks.every((check) => check.passed),
    checks,
  };
}

function renderWalletHandoffReadinessManifest(intent) {
  const manifest = buildWalletHandoffReadinessManifest(intent);
  walletHandoffReadinessList.replaceChildren(
    ...manifest.checks.map((check) => {
      const item = document.createElement('li');
      const strong = document.createElement('strong');
      strong.textContent = `${check.passed ? 'PASS' : 'BLOCK'} · ${check.label}`;
      item.append(strong, document.createTextNode(` — ${check.detail}`));
      return item;
    })
  );
  walletHandoffReadinessJson.textContent = JSON.stringify({
    walletRequestEnabled: manifest.walletRequestEnabled,
    canRequestWallet: manifest.canRequestWallet,
    sendPrRequired: manifest.sendPrRequired,
    allLocalPrerequisitesPassed: manifest.allLocalPrerequisitesPassed,
    requiredBeforeSend: manifest.requiredBeforeSend,
  }, null, 2);
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

function hasHumanApprovalMarker() {
  return currentStatus === 'approved_local' || currentStatus === 'final_review_confirmed';
}

function buildValidationSummary(intent) {
  const humanApprovalMarked = hasHumanApprovalMarker();
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
      passed: humanApprovalMarked,
      detail: humanApprovalMarked
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

function getFinalConfirmationReasons(intent) {
  const walletPreview = getWalletPreviewState(intent);
  const reasons = [];

  if (!isIntentReadyForReview(intent)) {
    reasons.push('Intent is not review-ready: fix recipient, amount, and expiry first.');
  }
  if (!frozenIntentSnapshot) {
    reasons.push('Frozen intent missing: prepare the intent before final confirmation.');
  }
  if (hasFrozenIntentChanged(intent)) {
    reasons.push('Frozen intent changed: restart review before final confirmation.');
  }
  if (currentStatus !== 'approved_local' && currentStatus !== 'final_review_confirmed') {
    reasons.push('Local approval missing: click Approve manually before final confirmation.');
  }
  if (!finalConfirmationCheckbox.checked) {
    reasons.push('Final review checkbox is not checked.');
  }
  if (!walletPreview.chainMatches) {
    reasons.push('Arc Testnet chain is not observed; this remains a no-transaction confirmation.');
  }
  reasons.push('Transaction request remains disabled until a separate reviewed testnet send PR.');

  return reasons;
}

function canRecordFinalConfirmation(intent) {
  return isIntentReadyForReview(intent)
    && Boolean(frozenIntentSnapshot)
    && !hasFrozenIntentChanged(intent)
    && currentStatus === 'approved_local'
    && finalConfirmationCheckbox.checked;
}

function renderFinalConfirmationPanel(intent) {
  const canConfirm = canRecordFinalConfirmation(intent);
  finalConfirmationButton.disabled = !canConfirm;
  finalConfirmationButton.setAttribute('aria-disabled', canConfirm ? 'false' : 'true');
  finalConfirmationReasons.replaceChildren(
    ...getFinalConfirmationReasons(intent).map((reason) => {
      const item = document.createElement('li');
      item.textContent = reason;
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
    unsignedTransactionDraft: buildUnsignedTransactionDraft(intent),
    transactionDraftConsistency: buildTransactionDraftConsistencyCheck(intent),
    walletHandoffReadiness: buildWalletHandoffReadinessManifest(intent),
    validationSummary: buildValidationSummary(intent),
    walletPreview: getWalletPreviewState(intent),
    frozenIntent: frozenIntentSnapshot ? frozenIntentSnapshot.fields : null,
    finalConfirmation: {
      recorded: finalConfirmationRecorded,
      checkboxChecked: finalConfirmationCheckbox.checked,
      canConfirmLocally: canRecordFinalConfirmation(intent),
      reasons: getFinalConfirmationReasons(intent),
      transactionRequestEnabled: false,
    },
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
        passed: hasHumanApprovalMarker(),
        required: true,
        note: 'Local approval is only a review marker, not wallet consent.',
      },
      transactionDraftConsistency: {
        passed: buildTransactionDraftConsistencyCheck(intent).allPassed,
        required: true,
        note: 'Unsigned draft must decode back to reviewed intent fields before wallet handoff.',
      },
      walletHandoffReadiness: {
        passed: buildWalletHandoffReadinessManifest(intent).allLocalPrerequisitesPassed,
        required: true,
        note: 'Future send PR remains blocked until every handoff-readiness guard is satisfied.',
      },
      finalConfirmation: {
        passed: finalConfirmationRecorded,
        required: true,
        note: 'Final confirmation is local UX only; it never enables a transaction request.',
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
  renderUnsignedTransactionDraft(intent);
  renderTransactionDraftConsistencyCheck(intent);
  renderWalletHandoffReadinessManifest(intent);
  renderValidationSummary(intent);
  renderSigningPreflightReport(intent);
  renderFinalConfirmationPanel(intent);
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
  finalConfirmationRecorded = false;
  render();
});

finalConfirmationCheckbox.addEventListener('change', () => {
  finalConfirmationRecorded = false;
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
  finalConfirmationRecorded = false;
  appendEvent('approved_local', 'Human approval was recorded as local UI state only for the frozen intent.');
});

finalConfirmationButton.addEventListener('click', () => {
  const intent = readIntent();
  if (!canRecordFinalConfirmation(intent)) {
    appendEvent('approved_local', 'Final confirmation stayed blocked until the frozen reviewed intent passes every local gate.');
    return;
  }
  finalConfirmationRecorded = true;
  appendEvent('final_review_confirmed', 'Final local confirmation recorded. Transaction requests remain disabled.');
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
  finalConfirmationRecorded = false;
  form.reset();
  finalConfirmationCheckbox.checked = false;
  render();
});

renderArcStatusPanel();
render();

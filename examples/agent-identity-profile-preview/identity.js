const ARC_IDENTITY_PREVIEW = Object.freeze({
  network: {
    name: 'arc-testnet',
    chainId: 5042002,
    chainIdHex: '0x4cef52',
  },
  registries: {
    identityRegistry: '0x8004A818BFB912233c491871b3d84c89A494BD9e',
    reputationRegistry: '0x8004B663056A597Dffe9eCcC1965A193B7388713',
    validationRegistry: '0x8004Cb1BF31DAf7788923b405b754f57acEB4272',
  },
});

const fields = {
  name: document.querySelector('#agent-name'),
  type: document.querySelector('#agent-type'),
  capabilities: document.querySelector('#capabilities'),
  controller: document.querySelector('#controller-note'),
  reputation: document.querySelector('#reputation-note'),
  validation: document.querySelector('#validation-note'),
};
const nodes = {
  status: document.querySelector('#status-badge'),
  registries: document.querySelector('#registry-json'),
  safety: document.querySelector('#safety-json'),
  profile: document.querySelector('#profile-json'),
};
const buttons = {
  freeze: document.querySelector('#freeze-profile'),
  reset: document.querySelector('#reset-profile'),
};

let state = 'draft_profile';
let frozenAt = null;

function capabilitiesList() {
  return fields.capabilities.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function safetyFlags() {
  return {
    localOnly: true,
    statusImpliesRegistration: false,
    walletConnected: false,
    walletActionEnabled: false,
    metadataUploaded: false,
    registrationTransactionPrepared: false,
    reputationTransactionPrepared: false,
    validationTransactionPrepared: false,
    signingEnabled: false,
    transactionBroadcast: false,
    backendCalls: false,
    remoteRpcCalls: false,
    humanApprovalRequired: true,
    mainnetEnabled: false,
  };
}

function profileObject() {
  return {
    schema: 'arc-mcp-builder-assistant.agentIdentity.preview.v1',
    state,
    status: 'unregistered_local_preview',
    frozenAt,
    sourceGrounding: [
      'https://docs.arc.network/arc/tutorials/register-your-first-ai-agent',
      'https://docs.arc.network/build/agentic-economy',
    ],
    network: ARC_IDENTITY_PREVIEW.network,
    registries: ARC_IDENTITY_PREVIEW.registries,
    profile: {
      name: fields.name.value.trim(),
      agentType: fields.type.value.trim(),
      capabilities: capabilitiesList(),
      metadataUri: 'not_uploaded',
      agentId: 'unknown_until_registered',
      ownerAddress: 'unknown_until_wallet_confirmed',
      validatorAddress: 'unknown_until_validator_selected',
    },
    review: {
      controllerNote: fields.controller.value.trim(),
      reputationNote: fields.reputation.value.trim(),
      validationRequirement: fields.validation.value.trim(),
      ownerCannotSelfValidate: true,
      futureRegistrationRequiresSeparatePr: true,
    },
    safety: safetyFlags(),
  };
}

function render() {
  const profile = profileObject();
  nodes.status.textContent = state;
  nodes.registries.textContent = JSON.stringify(ARC_IDENTITY_PREVIEW.registries, null, 2);
  nodes.safety.textContent = JSON.stringify(safetyFlags(), null, 2);
  nodes.profile.textContent = JSON.stringify(profile, null, 2);
  buttons.freeze.disabled = state === 'profile_frozen_for_review';
}

buttons.freeze.addEventListener('click', () => {
  state = 'profile_frozen_for_review';
  frozenAt = new Date().toISOString();
  render();
});
buttons.reset.addEventListener('click', () => {
  state = 'draft_profile';
  frozenAt = null;
  fields.name.value = 'Research Buyer Agent';
  fields.type.value = 'research';
  fields.capabilities.value = 'quote-paid-data, prepare-payment-intent, explain-source-cost';
  fields.controller.value = 'Controller address is unknown until a reviewed wallet integration exists.';
  fields.reputation.value = 'External validators should record feedback only after observable outcomes.';
  fields.validation.value = 'Validation status remains unknown until an external validator responds on Arc Testnet.';
  render();
});
for (const field of Object.values(fields)) {
  field.addEventListener('input', render);
}
render();

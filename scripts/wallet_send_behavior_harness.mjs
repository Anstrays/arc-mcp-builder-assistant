#!/usr/bin/env node
// Dependency-free behavioral harness for the guarded Arc Testnet wallet page.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = fs.readFileSync(
  path.join(ROOT, 'examples', 'arc-testnet-wallet-send-gate', 'wallet-send-gate.js'),
  'utf8',
);
const ACCOUNT = '0x2222222222222222222222222222222222222222';
const RECIPIENT = '0x1111111111111111111111111111111111111111';
const ARC_CHAIN = '0x4cef52';
const TX_HASH = `0x${'a'.repeat(64)}`;
const EXPECTED_DATA = `0xa9059cbb${'0'.repeat(24)}${'1'.repeat(40)}${'0'.repeat(60)}2710`;

class FakeElement {
  constructor(id) {
    this.id = id;
    this.value = '';
    this.checked = false;
    this.disabled = false;
    this.hidden = false;
    this.href = '';
    this.className = '';
    this.textContent = '';
    this.children = [];
    this.listeners = new Map();
  }

  addEventListener(type, callback) {
    const callbacks = this.listeners.get(type) || [];
    callbacks.push(callback);
    this.listeners.set(type, callbacks);
  }

  append(...children) {
    this.children.push(...children);
  }

  replaceChildren(...children) {
    this.children = children;
  }

  async trigger(type) {
    if (type === 'click' && this.disabled) return;
    const callbacks = this.listeners.get(type) || [];
    await Promise.all(callbacks.map((callback) => callback({ type, target: this })));
  }
}

class FakeProvider {
  constructor({ chainId = ARC_CHAIN, rejectSend = false } = {}) {
    this.account = ACCOUNT;
    this.chainId = chainId;
    this.rejectSend = rejectSend;
    this.calls = [];
    this.listeners = new Map();
  }

  on(event, callback) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.push(callback);
    this.listeners.set(event, callbacks);
  }

  emit(event, value) {
    for (const callback of this.listeners.get(event) || []) callback(value);
  }

  async request(request) {
    this.calls.push(structuredClone(request));
    switch (request.method) {
      case 'eth_requestAccounts':
      case 'eth_accounts':
        return [this.account];
      case 'eth_chainId':
        return this.chainId;
      case 'wallet_switchEthereumChain':
      case 'wallet_addEthereumChain':
        this.chainId = request.params[0].chainId;
        return null;
      case 'eth_sendTransaction':
        if (this.rejectSend) throw Object.assign(new Error('rejected'), { code: 4001 });
        return TX_HASH;
      default:
        throw new Error(`unexpected fake-provider method: ${request.method}`);
    }
  }
}

function createHarness({ gated = false, provider = new FakeProvider() } = {}) {
  const ids = [
    'feature-gate-status', 'risk-acknowledgement', 'wallet-status', 'provider-state',
    'account-state', 'chain-state', 'connect-wallet', 'switch-network', 'recipient',
    'amount', 'expiry', 'memo', 'freeze-intent', 'intent-status', 'frozen-payload',
    'confirmation-phrase', 'final-send-confirmation', 'send-transaction', 'send-status',
    'send-result', 'transaction-link', 'guard-list', 'method-log',
  ];
  const elements = new Map(ids.map((id) => [id, new FakeElement(id)]));
  elements.get('amount').value = '0.01';
  elements.get('memo').value = 'Manual Arc Testnet builder-kit transfer';
  elements.get('transaction-link').hidden = true;

  const document = {
    querySelector(selector) {
      return elements.get(selector.replace(/^#/, '')) || null;
    },
    createElement(tag) {
      return new FakeElement(tag);
    },
  };
  const window = {
    location: { search: gated ? '?enableArcTestnetSend=reviewed-testnet-only' : '' },
    ethereum: provider,
  };
  window.top = window;
  window.self = window;
  const context = vm.createContext({
    console,
    document,
    window,
    URLSearchParams,
    Date,
    BigInt,
    RegExp,
    Error,
    Object,
    Array,
    String,
    Number,
    Boolean,
    JSON,
    Math,
  });
  vm.runInContext(SOURCE, context, { filename: 'wallet-send-gate.js' });
  return { elements, provider };
}

async function prepareFrozenIntent(harness) {
  const { elements } = harness;
  elements.get('risk-acknowledgement').checked = true;
  await elements.get('risk-acknowledgement').trigger('change');
  await elements.get('connect-wallet').trigger('click');
  elements.get('recipient').value = RECIPIENT;
  await elements.get('recipient').trigger('input');
  await elements.get('freeze-intent').trigger('click');
  assert.match(elements.get('frozen-payload').textContent, /guarded_arc_testnet_erc20_transfer/);
}

async function enableFinalConfirmation(harness) {
  const { elements } = harness;
  elements.get('confirmation-phrase').value = 'SEND ARC TESTNET USDC';
  elements.get('final-send-confirmation').checked = true;
  await elements.get('confirmation-phrase').trigger('input');
  await elements.get('final-send-confirmation').trigger('change');
  assert.equal(elements.get('send-transaction').disabled, false);
}

async function testDefaultDisabled() {
  const harness = createHarness();
  assert.deepEqual(harness.provider.calls, []);
  for (const id of ['risk-acknowledgement', 'connect-wallet', 'switch-network', 'freeze-intent', 'send-transaction']) {
    assert.equal(harness.elements.get(id).disabled, true, `${id} must be disabled without query gate`);
  }
}

async function testExactOneShotSend() {
  const harness = createHarness({ gated: true });
  assert.deepEqual(harness.provider.calls, []);
  await prepareFrozenIntent(harness);
  await enableFinalConfirmation(harness);

  const first = harness.elements.get('send-transaction').trigger('click');
  const second = harness.elements.get('send-transaction').trigger('click');
  await Promise.all([first, second]);

  const sends = harness.provider.calls.filter((call) => call.method === 'eth_sendTransaction');
  assert.equal(sends.length, 1);
  assert.deepEqual(sends[0].params, [{
    chainId: ARC_CHAIN,
    from: ACCOUNT,
    to: '0x3600000000000000000000000000000000000000',
    value: '0x0',
    data: EXPECTED_DATA,
  }]);
  assert.equal(harness.elements.get('send-status').textContent, 'submitted / pending');
  assert.equal(harness.elements.get('transaction-link').hidden, false);
  assert.match(harness.elements.get('transaction-link').href, new RegExp(`${TX_HASH}$`));
}

async function testWrongChainAndAccountChangeBlock() {
  const wrongChain = createHarness({ gated: true, provider: new FakeProvider({ chainId: '0x1' }) }); // do not use: negative test fixture
  wrongChain.elements.get('risk-acknowledgement').checked = true;
  await wrongChain.elements.get('risk-acknowledgement').trigger('change');
  await wrongChain.elements.get('connect-wallet').trigger('click');
  assert.equal(wrongChain.elements.get('freeze-intent').disabled, true);
  assert.equal(wrongChain.elements.get('send-transaction').disabled, true);
  assert.equal(wrongChain.provider.calls.some((call) => call.method === 'eth_sendTransaction'), false);

  const changedAccount = createHarness({ gated: true });
  await prepareFrozenIntent(changedAccount);
  changedAccount.provider.account = '0x3333333333333333333333333333333333333333';
  changedAccount.provider.emit('accountsChanged', [changedAccount.provider.account]);
  assert.match(changedAccount.elements.get('frozen-payload').textContent, /Wallet account changed/);
  assert.equal(changedAccount.elements.get('send-transaction').disabled, true);
}

async function testRejectionKeepsOneShotLock() {
  const harness = createHarness({ gated: true, provider: new FakeProvider({ rejectSend: true }) });
  await prepareFrozenIntent(harness);
  await enableFinalConfirmation(harness);
  await harness.elements.get('send-transaction').trigger('click');

  assert.equal(
    harness.provider.calls.filter((call) => call.method === 'eth_sendTransaction').length,
    1,
  );
  assert.equal(harness.elements.get('send-transaction').disabled, true);
  assert.equal(harness.elements.get('send-status').textContent, 'attempt locked');
  assert.equal(harness.elements.get('transaction-link').hidden, true);
  assert.equal(harness.elements.get('send-result').textContent, 'Wallet request was rejected by the user.');
}

await testDefaultDisabled();
await testExactOneShotSend();
await testWrongChainAndAccountChangeBlock();
await testRejectionKeepsOneShotLock();
console.log('guarded wallet behavior harness passed: default lock, exact one-shot send, wrong-chain/account-change blocks, rejection lock');

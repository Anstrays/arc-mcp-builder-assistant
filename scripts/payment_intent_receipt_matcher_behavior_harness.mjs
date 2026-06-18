#!/usr/bin/env node
// Dependency-free behavioral harness for the payment-intent receipt matcher.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = fs.readFileSync(
  path.join(ROOT, 'examples', 'payment-intent-receipt-matcher', 'matcher.js'),
  'utf8',
);
const HASH = `0x${'b'.repeat(64)}`;
const WRONG_HASH = `0x${'c'.repeat(64)}`;
const USDC = '0x3600000000000000000000000000000000000000';
const FROM = '0x2222222222222222222222222222222222222222';
const TO = '0x1111111111111111111111111111111111111111';
const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const TOPIC_FROM = `0x${'0'.repeat(24)}${FROM.slice(2)}`;
const TOPIC_TO = `0x${'0'.repeat(24)}${TO.slice(2)}`;
const TEN_THOUSAND_BASE_UNITS = `0x${'0'.repeat(60)}2710`;

const SAMPLE_INTENT = {
  version: '2025-06-arc-payment-intent-v1',
  network: 'Arc Testnet',
  chainId: 5042002,
  asset: 'USDC',
  token: USDC,
  recipient: TO,
  amount: '0.01',
  amountBaseUnits: '10000',
  decimals: 6,
};

class FakeElement {
  constructor(id) {
    this.id = id;
    this.value = '';
    this.className = '';
    this.textContent = '';
    this.children = [];
    this.disabled = false;
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
    await Promise.all((this.listeners.get(type) || []).map((callback) => callback({ type, target: this })));
  }
}

function baseReceipt(overrides = {}) {
  return {
    transactionHash: HASH,
    blockNumber: '0x10',
    gasUsed: '0x5208',
    status: '0x1',
    logs: [
      {
        address: USDC,
        topics: [TRANSFER_TOPIC, TOPIC_FROM, TOPIC_TO],
        data: TEN_THOUSAND_BASE_UNITS,
        logIndex: '0x0',
        transactionIndex: '0x0',
      },
    ],
    ...overrides,
  };
}

function createHarness({
  chainId = '0x4cef52',
  receipt = baseReceipt(),
  responseOverride = null,
  fetchError = null,
} = {}) {
  const ids = [
    'payment-intent', 'transaction-hash', 'match-receipt', 'reset-matcher', 'status-pill',
    'match-summary-list', 'transfer-log-list', 'match-json',
  ];
  const elements = new Map(ids.map((id) => [id, new FakeElement(id)]));
  elements.get('transaction-hash').value = HASH;
  elements.get('payment-intent').value = JSON.stringify(SAMPLE_INTENT);
  const calls = [];
  const results = {
    eth_chainId: chainId,
    eth_getTransactionReceipt: receipt,
  };
  const fetch = async (_url, request) => {
    const body = JSON.parse(request.body);
    calls.push(body.method);
    if (fetchError) throw fetchError;
    return {
      ok: true,
      async text() {
        const defaultResponse = { jsonrpc: '2.0', id: body.id, result: results[body.method] };
        return JSON.stringify(responseOverride ? responseOverride(body, defaultResponse) : defaultResponse);
      },
    };
  };
  const document = {
    querySelector(selector) {
      return elements.get(selector.replace(/^#/, '')) || null;
    },
    createElement(tag) {
      return new FakeElement(tag);
    },
  };
  const context = vm.createContext({
    console,
    document,
    window: { setTimeout, clearTimeout },
    fetch,
    AbortController,
    TextEncoder,
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
  vm.runInContext(SOURCE, context, { filename: 'matcher.js' });
  return { elements, calls };
}

function result(harness) {
  return JSON.parse(harness.elements.get('match-json').textContent);
}

async function testMatchWhenTransferMatchesIntent() {
  const harness = createHarness();
  await harness.elements.get('match-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'match');
  assert.equal(value.evidenceVerdict, 'intent_receipt_match_observed');
  assert.equal(value.intentMatched, true);
  assert.equal(value.matchingTransferCount, 1);
  assert.equal(value.transferEventCount, 1);
  assert.equal(value.settlementProven, false);
  assert.equal(value.businessAcceptanceProven, false);
  assert.deepEqual(harness.calls, ['eth_chainId', 'eth_getTransactionReceipt']);
}

async function testMismatchWhenRecipientDiffers() {
  const receipt = baseReceipt({
    logs: [
      {
        address: USDC,
        topics: [TRANSFER_TOPIC, TOPIC_FROM, `0x${'0'.repeat(24)}3333333333333333333333333333333333333333`],
        data: TEN_THOUSAND_BASE_UNITS,
        logIndex: '0x0',
        transactionIndex: '0x0',
      },
    ],
  });
  const harness = createHarness({ receipt });
  await harness.elements.get('match-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'mismatch');
  assert.equal(value.evidenceVerdict, 'intent_receipt_mismatch');
  assert.equal(value.intentMatched, false);
  assert.equal(value.matchingTransferCount, 0);
}

async function testRevertedReceiptAndNullReceipt() {
  const reverted = createHarness({ receipt: baseReceipt({ status: '0x0', logs: [] }) });
  await reverted.elements.get('match-receipt').trigger('click');
  const revertedValue = result(reverted);
  assert.equal(revertedValue.state, 'revert');
  assert.equal(revertedValue.evidenceVerdict, 'reverted_receipt_observed');
  assert.equal(revertedValue.intentMatched, false);

  const missing = createHarness({ receipt: null });
  await missing.elements.get('match-receipt').trigger('click');
  const missingValue = result(missing);
  assert.equal(missingValue.state, 'not_found');
  assert.equal(missingValue.evidenceVerdict, 'receipt_not_found');
  assert.equal(missingValue.intentMatched, false);
}

async function testWrongChainStopsBeforeReceipt() {
  const harness = createHarness({ chainId: '0x1' });
  await harness.elements.get('match-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.equal(value.evidenceVerdict, 'unknown_wrong_chain');
  assert.equal(value.rpcChainIdMatchesArcTestnet, false);
  assert.deepEqual(harness.calls, ['eth_chainId']);
}

async function testInvalidHashOrIntentAvoidsRpc() {
  const harness = createHarness();
  harness.elements.get('transaction-hash').value = 'not-a-hash';
  await harness.elements.get('match-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.equal(value.evidenceVerdict, 'invalid_local_input');
  assert.deepEqual(harness.calls, []);

  const badIntent = createHarness();
  badIntent.elements.get('payment-intent').value = 'not-json';
  await badIntent.elements.get('match-receipt').trigger('click');
  const badIntentValue = result(badIntent);
  assert.equal(badIntentValue.state, 'unknown');
  assert.equal(badIntentValue.evidenceVerdict, 'invalid_local_input');
  assert.deepEqual(badIntent.calls, []);
}

function invalidIntentHarness(intentPatch) {
  const harness = createHarness();
  const patched = { ...SAMPLE_INTENT, ...intentPatch };
  harness.elements.get('payment-intent').value = JSON.stringify(patched);
  return harness;
}

async function testInvalidLocalIntentAvoidsRpc() {
  const cases = [
    { patch: { chainId: 1 }, name: 'wrong chainId' },
    { patch: { network: 'Ethereum Mainnet' }, name: 'wrong network' },
    { patch: { asset: 'DAI' }, name: 'wrong asset' },
    { patch: { token: '0x2222222222222222222222222222222222222222' }, name: 'non-USDC token' },
    { patch: { decimals: 18 }, name: 'wrong decimals' },
    { patch: { recipient: '0x0000000000000000000000000000000000000000' }, name: 'zero recipient' },
    { patch: { recipient: USDC }, name: 'recipient is USDC contract' },
    { patch: { amount: '0.0100009', amountBaseUnits: undefined }, name: 'too many fractional digits' },
    { patch: { amount: '0', amountBaseUnits: undefined }, name: 'zero amount' },
    { patch: { amount: '-1', amountBaseUnits: undefined }, name: 'negative amount' },
    { patch: { amountBaseUnits: '0x2710', amount: undefined }, name: 'hex amountBaseUnits' },
    { patch: { amountBaseUnits: '0', amount: undefined }, name: 'zero amountBaseUnits' },
    { patch: { amountBaseUnits: '-1', amount: undefined }, name: 'negative amountBaseUnits' },
    { patch: { amountBaseUnits: '1.5', amount: undefined }, name: 'decimal amountBaseUnits' },
    { patch: { amountBaseUnits: '1e6', amount: undefined }, name: 'scientific amountBaseUnits' },
    { patch: { amount: '1' + '0'.repeat(78), amountBaseUnits: undefined }, name: 'oversized decimal amount' },
    { patch: { amountBaseUnits: '9'.repeat(79), amount: undefined }, name: 'oversized amountBaseUnits' },
    { patch: { amount: '0.02', amountBaseUnits: '10000' }, name: 'mismatched amount/baseUnits' },
    { patch: { amount: '1,000', amountBaseUnits: undefined }, name: 'comma-separated amount' },
    { patch: { amount: '1e6', amountBaseUnits: undefined }, name: 'scientific decimal amount' },
  ];
  for (const { patch, name } of cases) {
    const harness = invalidIntentHarness(patch);
    await harness.elements.get('match-receipt').trigger('click');
    const value = result(harness);
    assert.equal(value.state, 'unknown', `expected state 'unknown' for ${name}, got '${value.state}'`);
    assert.equal(value.evidenceVerdict, 'invalid_local_input', `expected verdict 'invalid_local_input' for ${name}, got '${value.evidenceVerdict}'`);
    assert.deepEqual(harness.calls, [], `expected no RPC calls for ${name}, got ${JSON.stringify(harness.calls)}`);
  }
}

async function testRpcEnvelopeAndHashBindingFailClosed() {
  const wrongEnvelope = createHarness({
    responseOverride(_body, response) {
      return { ...response, id: 'wrong-response-id' };
    },
  });
  await wrongEnvelope.elements.get('match-receipt').trigger('click');
  const envelopeFailure = result(wrongEnvelope);
  assert.equal(envelopeFailure.state, 'unknown');
  assert.equal(envelopeFailure.evidenceVerdict, 'unknown_rpc_unavailable');
  assert.match(envelopeFailure.reason, /envelope did not match/);
  assert.deepEqual(wrongEnvelope.calls, ['eth_chainId']);

  const wrongHash = createHarness({ receipt: baseReceipt({ transactionHash: WRONG_HASH }) });
  await wrongHash.elements.get('match-receipt').trigger('click');
  const hashMismatch = result(wrongHash);
  assert.equal(hashMismatch.state, 'unknown');
  assert.equal(hashMismatch.evidenceVerdict, 'unknown_hash_mismatch');
  assert.equal(hashMismatch.receiptHashMatches, false);
  assert.equal(hashMismatch.intentMatched, false);
}

await testMatchWhenTransferMatchesIntent();
await testMismatchWhenRecipientDiffers();
await testRevertedReceiptAndNullReceipt();
await testWrongChainStopsBeforeReceipt();
await testInvalidHashOrIntentAvoidsRpc();
await testInvalidLocalIntentAvoidsRpc();
await testRpcEnvelopeAndHashBindingFailClosed();
console.log('payment intent receipt matcher behavior harness passed: match/mismatch/revert/not-found, wrong-chain stop, invalid-input no-RPC, invalid-local-intent no-RPC, envelope/hash binding');

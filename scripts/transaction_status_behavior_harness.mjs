#!/usr/bin/env node
// Dependency-free behavioral harness for read-only transaction evidence.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = fs.readFileSync(
  path.join(ROOT, 'examples', 'transaction-status-playground', 'status.js'),
  'utf8',
);
const HASH = `0x${'b'.repeat(64)}`;
const RECIPIENT = '0x1111111111111111111111111111111111111111';
const USDC = '0x3600000000000000000000000000000000000000';
const DATA = `0xa9059cbb${'0'.repeat(24)}${'1'.repeat(40)}${'0'.repeat(60)}2710`;

class FakeElement {
  constructor(id) {
    this.id = id;
    this.value = '';
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
    await Promise.all((this.listeners.get(type) || []).map((callback) => callback({ type, target: this })));
  }
}

function createHarness({
  chainId = '0x4cef52',
  recipient = RECIPIENT,
  transactionHash = HASH,
  receiptHash = HASH,
  responseOverride = null,
} = {}) {
  const ids = [
    'transaction-hash', 'expected-recipient', 'expected-amount', 'check-transaction',
    'reset-transaction', 'status-pill', 'status-check-list', 'transaction-status-json',
  ];
  const elements = new Map(ids.map((id) => [id, new FakeElement(id)]));
  elements.get('transaction-hash').value = HASH;
  elements.get('expected-recipient').value = recipient;
  elements.get('expected-amount').value = '0.01';

  const calls = [];
  const transaction = {
    hash: transactionHash,
    from: '0x2222222222222222222222222222222222222222',
    to: USDC,
    value: '0x0',
    input: DATA,
  };
  const receipt = { transactionHash: receiptHash, blockNumber: '0x10', status: '0x1' };
  const results = {
    eth_chainId: chainId,
    eth_getTransactionByHash: transaction,
    eth_getTransactionReceipt: receipt,
  };
  const fetch = async (_url, request) => {
    const body = JSON.parse(request.body);
    calls.push(body.method);
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
  vm.runInContext(SOURCE, context, { filename: 'status.js' });
  return { elements, calls };
}

function result(harness) {
  return JSON.parse(harness.elements.get('transaction-status-json').textContent);
}

async function testConfirmedExpectedTransferShape() {
  const harness = createHarness();
  await harness.elements.get('check-transaction').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'confirmed');
  assert.equal(value.evidenceVerdict, 'confirmed_expected_transfer_shape');
  assert.equal(value.transferReview.state, 'match');
  assert.equal(value.transferReview.allMatched, true);
  assert.equal(value.settlementProven, false);
  assert.equal(value.businessAcceptanceProven, false);
  assert.deepEqual(harness.calls, [
    'eth_chainId',
    'eth_getTransactionByHash',
    'eth_getTransactionReceipt',
  ]);
}

async function testMismatchAndWrongChainFailClosed() {
  const mismatch = createHarness({ recipient: '0x3333333333333333333333333333333333333333' });
  await mismatch.elements.get('check-transaction').trigger('click');
  const mismatched = result(mismatch);
  assert.equal(mismatched.state, 'confirmed');
  assert.equal(mismatched.evidenceVerdict, 'mismatch_expected_transfer');
  assert.equal(mismatched.transferReview.state, 'mismatch');
  assert.equal(mismatched.settlementProven, false);

  const wrongChain = createHarness({ chainId: '0x1' });
  await wrongChain.elements.get('check-transaction').trigger('click');
  const wrong = result(wrongChain);
  assert.equal(wrong.state, 'unknown');
  assert.equal(wrong.evidenceVerdict, 'unknown_wrong_chain');
  assert.equal(wrong.settlementProven, false);
  assert.deepEqual(wrongChain.calls, ['eth_chainId']);
}

async function testInvalidExpectedFieldsAvoidRpc() {
  const harness = createHarness();
  harness.elements.get('expected-amount').value = '0';
  await harness.elements.get('check-transaction').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.match(value.reason, /greater than zero/);
  assert.deepEqual(harness.calls, []);
}

async function testRpcEnvelopeAndHashBindingFailClosed() {
  const wrongHash = createHarness({ transactionHash: `0x${'c'.repeat(64)}` });
  await wrongHash.elements.get('check-transaction').trigger('click');
  const hashMismatch = result(wrongHash);
  assert.equal(hashMismatch.state, 'unknown');
  assert.equal(hashMismatch.evidenceVerdict, 'unknown_hash_mismatch');
  assert.equal(hashMismatch.rpcObjectHashesMatch, false);
  assert.equal(hashMismatch.transferReview.state, 'unknown');
  assert.equal(hashMismatch.settlementProven, false);

  const wrongEnvelope = createHarness({
    responseOverride(_body, response) {
      return { ...response, id: 'wrong-response-id' };
    },
  });
  await wrongEnvelope.elements.get('check-transaction').trigger('click');
  const envelopeFailure = result(wrongEnvelope);
  assert.equal(envelopeFailure.state, 'unknown');
  assert.equal(envelopeFailure.evidenceVerdict, 'unknown_rpc_unavailable');
  assert.match(envelopeFailure.reason, /envelope did not match/);
  assert.deepEqual(wrongEnvelope.calls, ['eth_chainId']);
}

await testConfirmedExpectedTransferShape();
await testMismatchAndWrongChainFailClosed();
await testInvalidExpectedFieldsAvoidRpc();
await testRpcEnvelopeAndHashBindingFailClosed();
console.log('transaction status behavior harness passed: transfer match/mismatch, chain-first stop, hash binding, RPC envelope, invalid-input no-RPC');

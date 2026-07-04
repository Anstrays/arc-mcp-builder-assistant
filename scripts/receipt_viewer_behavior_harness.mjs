#!/usr/bin/env node
// Dependency-free behavioral harness for the read-only receipt viewer.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE = fs.readFileSync(
  path.join(ROOT, 'examples', 'receipt-viewer', 'receipt-viewer.js'),
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
    'transaction-hash', 'load-receipt', 'reset-receipt', 'status-pill',
    'receipt-summary-list', 'transfer-log-list', 'receipt-json',
  ];
  const elements = new Map(ids.map((id) => [id, new FakeElement(id)]));
  elements.get('transaction-hash').value = HASH;
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
  vm.runInContext(SOURCE, context, { filename: 'receipt-viewer.js' });
  return { elements, calls };
}

function result(harness) {
  return JSON.parse(harness.elements.get('receipt-json').textContent);
}

async function testSuccessfulReceiptHighlightsUsdcTransfer() {
  const harness = createHarness();
  await harness.elements.get('load-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'success');
  assert.equal(value.evidenceVerdict, 'success_receipt_observed');
  assert.equal(value.blockNumberDecimal, '16');
  assert.equal(value.gasUsedDecimal, '21000');
  assert.equal(value.transferEventCount, 1);
  assert.equal(value.transferEvents[0].from, FROM);
  assert.equal(value.transferEvents[0].to, TO);
  assert.equal(value.transferEvents[0].amountBaseUnits, '10000');
  assert.equal(value.transferEvents[0].amountUsdc, '0.01');
  assert.equal(value.settlementProven, false);
  assert.equal(value.businessAcceptanceProven, false);
  assert.deepEqual(harness.calls, ['eth_chainId', 'eth_getTransactionReceipt']);
}

async function testRevertedReceiptAndNullReceipt() {
  const reverted = createHarness({ receipt: baseReceipt({ status: '0x0', logs: [] }) });
  await reverted.elements.get('load-receipt').trigger('click');
  const revertedValue = result(reverted);
  assert.equal(revertedValue.state, 'revert');
  assert.equal(revertedValue.evidenceVerdict, 'reverted_receipt_observed');
  assert.equal(revertedValue.transferEventCount, 0);

  const missing = createHarness({ receipt: null });
  await missing.elements.get('load-receipt').trigger('click');
  const missingValue = result(missing);
  assert.equal(missingValue.state, 'not_found');
  assert.equal(missingValue.evidenceVerdict, 'receipt_not_found');
  assert.equal(missingValue.receiptFound, false);
}

async function testWrongChainStopsBeforeReceipt() {
  const harness = createHarness({ chainId: '0x1' }); // do not use: negative test fixture
  await harness.elements.get('load-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.equal(value.evidenceVerdict, 'unknown_wrong_chain');
  assert.equal(value.rpcChainIdMatchesArcTestnet, false);
  assert.deepEqual(harness.calls, ['eth_chainId']);
}

async function testInvalidHashAvoidsRpc() {
  const harness = createHarness();
  harness.elements.get('transaction-hash').value = 'not-a-hash';
  await harness.elements.get('load-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.equal(value.evidenceVerdict, 'invalid_local_input');
  assert.match(value.reason, /32-byte/);
  assert.deepEqual(harness.calls, []);
}

async function testRpcEnvelopeAndHashBindingFailClosed() {
  const wrongEnvelope = createHarness({
    responseOverride(_body, response) {
      return { ...response, id: 'wrong-response-id' };
    },
  });
  await wrongEnvelope.elements.get('load-receipt').trigger('click');
  const envelopeFailure = result(wrongEnvelope);
  assert.equal(envelopeFailure.state, 'unknown');
  assert.equal(envelopeFailure.evidenceVerdict, 'unknown_rpc_unavailable');
  assert.match(envelopeFailure.reason, /envelope did not match/);
  assert.deepEqual(wrongEnvelope.calls, ['eth_chainId']);

  const wrongHash = createHarness({ receipt: baseReceipt({ transactionHash: WRONG_HASH }) });
  await wrongHash.elements.get('load-receipt').trigger('click');
  const hashMismatch = result(wrongHash);
  assert.equal(hashMismatch.state, 'unknown');
  assert.equal(hashMismatch.evidenceVerdict, 'unknown_hash_mismatch');
  assert.equal(hashMismatch.receiptHashMatches, false);
  assert.equal(hashMismatch.transferEventCount, 0);
}

async function testTimeoutFailsClosed() {
  const timeout = Object.assign(new Error('aborted'), { name: 'AbortError' });
  const harness = createHarness({ fetchError: timeout });
  await harness.elements.get('load-receipt').trigger('click');
  const value = result(harness);
  assert.equal(value.state, 'unknown');
  assert.equal(value.evidenceVerdict, 'unknown_rpc_unavailable');
  assert.match(value.reason, /Request timed out after 15 seconds/);
  assert.deepEqual(harness.calls, ['eth_chainId']);
}

await testSuccessfulReceiptHighlightsUsdcTransfer();
await testRevertedReceiptAndNullReceipt();
await testWrongChainStopsBeforeReceipt();
await testInvalidHashAvoidsRpc();
await testRpcEnvelopeAndHashBindingFailClosed();
await testTimeoutFailsClosed();
console.log('receipt viewer behavior harness passed: success/revert/not-found, USDC logs, wrong-chain stop, invalid-input no-RPC, envelope/hash binding, timeout fail-closed');

// Agent commerce live — real on-chain evidence from Arc Testnet.
// This page shows static verified transaction data. No network calls.

const ARC_TESTNET_CHAIN_ID = 5042002;
const ARC_TESTNET_CHAIN_HEX = "0x4cef52";
const WALLET_ADDRESS = "0x0cd9b933302d90bfe295471deac7f4eafd9ea401";
const USDC_CONTRACT = "0x3600000000000000000000000000000000000000";
const EXPLORER_BASE = "https://testnet.arcscan.app";

const walletState = [
  ["Wallet address", "0x0cd9…a401"],
  ["Wallet type", "Circle agent (SCA)"],
  ["Chain", "Arc Testnet"],
  ["Chain ID", "5042002 / 0x4cef52"],
  ["USDC contract", "0x3600…0000"],
  ["USDC decimals", "6 (ERC-20) / 18 (native)"],
  ["Gateway domain", "26 (Arc)"],
  ["Session", "testnet (OTP)"],
  ["Starting balance", "20.00 USDC"],
  ["On-chain balance", "~14.05 USDC"],
  ["Gateway balance", "3.9965 USDC (Arc)"],
];

const transactions = [
  {
    op: "TRANSFER (faucet)",
    status: "COMPLETE",
    amount: "20 USDC",
    block: "48020204",
    txHash: "0xd52b5296112b3ef7e6…",
    detail: "Circle faucet drip: 20 USDC native + 20 USDC ERC-20",
  },
  {
    op: "TRANSFER (self-test)",
    status: "COMPLETE",
    amount: "1 USDC",
    block: "48020319",
    txHash: "0xb570a204eb4d81d361…",
    detail: "Self-transfer: wallet deployment and functionality test",
  },
  {
    op: "CCTP APPROVE",
    status: "COMPLETE",
    amount: "—",
    block: "48020338",
    txHash: "0x044184a5ce5760a276…",
    detail: "USDC approve for TokenMessengerV2 (CCTP bridge)",
  },
  {
    op: "CCTP BURN (bridge)",
    status: "COMPLETE",
    amount: "1 USDC",
    block: "48020350",
    txHash: "0x7855802e76412ee50a…",
    detail: "Bridge: Arc Testnet → Base Sepolia via CCTP (domain 26 → 6)",
  },
  {
    op: "TRANSFER (agent payment)",
    status: "COMPLETE",
    amount: "0.5 USDC",
    block: "48027390",
    txHash: "0x490df63904f7722c36…",
    detail: "Agent pays 0.5 USDC for paid API call simulation → 0xdEaD",
  },
  {
    op: "TRANSFER (micro-payment)",
    status: "COMPLETE",
    amount: "0.25 USDC",
    block: "48027419",
    txHash: "0xda2ed5d09c781cbf5c…",
    detail: "Agent pays 0.25 USDC for micro-service call → 0xdEaD",
  },
  {
    op: "GATEWAY DEPOSIT",
    status: "COMPLETE",
    amount: "5 USDC",
    block: "48028452",
    txHash: "0x2f458c54c4d65868170…",
    detail: "Deposit 5 USDC into Circle Gateway on Arc (domain 26) via direct",
  },
  {
    op: "GATEWAY WITHDRAW",
    status: "COMPLETE",
    amount: "1 USDC",
    block: "—",
    txHash: "0x3ffb115ba2c453f5c07…",
    detail: "Withdraw 1 USDC from Gateway back to wallet (fee: 0.0035)",
  },
];

const unitEconomics = [
  ["Starting balance", "20.00 USDC"],
  ["Total payments sent", "1.75 USDC"],
  ["Gateway deposit", "5.00 USDC"],
  ["Gateway withdraw", "1.00 USDC (fee: 0.0035)"],
  ["Gateway balance", "3.9965 USDC (domain 26)"],
  ["Total network fees", "~0.09 USDC"],
  ["Bridge amount", "1.00 USDC"],
  ["On-chain balance", "~14.05 USDC"],
  ["Cost per payment", "~0.004 USDC"],
  ["Total transactions", "10 (all COMPLETE)"],
];

function renderWalletState() {
  const el = document.getElementById("wallet-state");
  if (!el) return;
  el.innerHTML = walletState
    .map(
      (row) =>
        '<div class="info-row"><span class="info-label">' +
        row[0] +
        '</span><span class="info-value">' +
        row[1] +
        "</span></div>"
    )
    .join("");
}

function renderTxLog() {
  const el = document.getElementById("tx-log");
  if (!el) return;
  el.innerHTML = transactions
    .map(
      (tx) =>
        '<div class="tx-card">' +
        '<div class="tx-card-header">' +
        '<span class="tx-op">' +
        tx.op +
        '</span><span class="tx-status complete">' +
        tx.status +
        "</span></div>" +
        '<div class="tx-detail">Amount: <strong>' +
        tx.amount +
        "</strong> | Block: " +
        tx.block +
        "</div>" +
        '<div class="tx-detail tx-hash">Tx: ' +
        tx.txHash +
        "</div>" +
        '<div class="tx-detail">' +
        tx.detail +
        "</div></div>"
    )
    .join("");
}

function renderUnitEconomics() {
  const el = document.getElementById("unit-economics");
  if (!el) return;
  el.innerHTML = unitEconomics
    .map(
      (row) =>
        '<div class="info-row"><span class="info-label">' +
        row[0] +
        '</span><span class="info-value">' +
        row[1] +
        "</span></div>"
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", function () {
  renderWalletState();
  renderTxLog();
  renderUnitEconomics();
});

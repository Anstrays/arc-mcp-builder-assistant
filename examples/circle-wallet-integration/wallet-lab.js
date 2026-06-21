// Circle wallet integration lab — local-only preview, no network calls.
// This page does NOT connect to Circle, RPC, or any external service.
// Use the `circle` CLI for live operations.

const ARC_TESTNET_CHAIN_ID = 5042002;
const ARC_TESTNET_CHAIN_HEX = "0x4cef52";
const ARC_TESTNET_USDC = "0x3600000000000000000000000000000000000000";
const GATEWAY_DOMAIN_ARC = 26;

const circleWalletLab = {
  // Static preview data — replace with CLI output when running locally.
  walletAddress: "0x0cd9b933302d90bfe295471deac7f4eafd9ea401",
  session: "testnet",
  balances: {
    usdcErc20: "19",
    usdcNative: "19.99",
  },
  network: {
    name: "Arc Testnet",
    chainId: ARC_TESTNET_CHAIN_ID,
    chainIdHex: ARC_TESTNET_CHAIN_HEX,
    usdcContract: ARC_TESTNET_USDC,
    gatewayDomain: GATEWAY_DOMAIN_ARC,
  },
};

function shortAddr(addr) {
  if (!addr || addr.length < 10) return addr;
  return addr.slice(0, 6) + "…" + addr.slice(-4);
}

function renderStatus() {
  const el = document.getElementById("wallet-status");
  if (el) {
    el.textContent = "Session: " + circleWalletLab.session + " (preview)";
  }
  const sessEl = document.getElementById("wallet-session");
  if (sessEl) {
    sessEl.textContent = circleWalletLab.session;
  }
}

function renderAddress() {
  const el = document.getElementById("wallet-address");
  if (el) {
    el.textContent = shortAddr(circleWalletLab.walletAddress);
  }
}

function renderBalance() {
  const erc20 = document.getElementById("wallet-balance-erc20");
  if (erc20) {
    erc20.textContent = circleWalletLab.balances.usdcErc20 + " USDC (6 dec)";
  }
  const native = document.getElementById("wallet-balance-native");
  if (native) {
    native.textContent = circleWalletLab.balances.usdcNative + " USDC (18 dec)";
  }
}

function renderAll() {
  renderStatus();
  renderAddress();
  renderBalance();
}

document.addEventListener("DOMContentLoaded", function () {
  renderAll();

  const refreshBtn = document.getElementById("refresh-preview");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", function () {
      renderAll();
      refreshBtn.textContent = "Preview refreshed";
      setTimeout(function () {
        refreshBtn.textContent = "Refresh preview";
      }, 1500);
    });
  }

  const cliBtn = document.getElementById("show-cli");
  if (cliBtn) {
    cliBtn.addEventListener("click", function () {
      const out = document.getElementById("cli-output");
      if (out) {
        out.style.display = out.style.display === "none" ? "block" : "none";
        cliBtn.textContent = out.style.display === "none" ? "Show CLI commands" : "Hide CLI commands";
      }
    });
  }
});

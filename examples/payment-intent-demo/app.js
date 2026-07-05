// Arc Payment Intent Demo — frontend
// Interacts with the Python backend (server.py) via /api/* endpoints.
// No external dependencies, no secrets, ESTIMATE-ONLY by default.

(function () {
  "use strict";

  // ── DOM refs ──
  const $ = (sel) => document.querySelector(sel);

  const walletModeBadge  = $("#wallet-mode");
  const balanceAmount    = $("#balance-amount");
  const balanceNative    = $("#balance-native");
  const walletAddr       = $("#wallet-addr");
  const walletChain      = $("#wallet-chain");
  const walletBalStatus  = $("#wallet-balance-status");
  const networkInfo      = $("#network-info");
  const txList           = $("#tx-list");
  const intentList       = $("#intent-list");
  const intentForm       = $("#intent-form");
  const toastEl          = $("#toast");
  const refreshBtn       = $("#refresh-all");

  // ── toast ──
  let toastTimer;

  function showToast(msg, error) {
    if (toastTimer) clearTimeout(toastTimer);
    toastEl.textContent = msg;
    toastEl.className = "toast show" + (error ? " error" : "");
    toastTimer = setTimeout(function () {
      toastEl.className = "toast";
    }, 4500);
  }

  function hideToast() {
    if (toastTimer) clearTimeout(toastTimer);
    toastEl.className = "toast";
  }

  // ── API helpers ──
  function apiGet(path) {
    return fetch(path).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + r.statusText);
      return r.json();
    });
  }

  function apiPost(path, body) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) throw new Error(data.error || r.statusText);
        return data;
      });
    });
  }

  // ── format helpers ──
  function fmtAddr(a) {
    if (a && a.length > 12) return a.slice(0, 6) + "…" + a.slice(-4);
    return a || "--";
  }

  function escapeHtml(s) {
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  function badgeClass(status) {
    switch (status) {
      case "estimated":        return "estimated";
      case "pending_user_approval": return "pending";
      case "submitted":        return "submitted";
      case "confirmed":        return "confirmed";
      case "failed":           return "failed";
      default:                 return "";
    }
  }

  // ── wallet ──
  function refreshWallet() {
    walletModeBadge.textContent = "Loading";
    walletModeBadge.className = "badge";
    balanceAmount.textContent = "--";
    balanceNative.textContent = "--";
    walletAddr.textContent = "--";
    walletChain.textContent = "--";
    walletBalStatus.textContent = "Loading…";

    apiGet("/api/wallet").then(function (w) {
      walletAddr.textContent = fmtAddr(w.address);
      walletChain.textContent = w.chain;
      walletBalStatus.textContent = w.real_transfer_enabled ? "Real transfers ENABLED" : "Estimate-only";

      if (w.balance_ok && w.balances) {
        var bals = Array.isArray(w.balances) ? w.balances : [w.balances];
        var total = 0;
        var nativeBal = "0";
        bals.forEach(function (b) {
          var amt = parseFloat(b.balance || "0");
          total += amt;
          if ((b.tokenSymbol || "").toUpperCase() === "USDC" || (b.tokenAddress || "").toLowerCase() === "0x3600000000000000000000000000000000000000") {
            nativeBal = b.balance || "0";
          }
        });
        balanceAmount.textContent = total.toFixed(2) + " USDC";
        balanceNative.textContent = nativeBal + " USDC";
      } else {
        balanceAmount.textContent = w.balance_error || "Unavailable";
      }

      if (w.tx_ok && w.recent_transactions) {
        // Transactions are rendered by refreshTx() — avoid race
      }
    }).catch(function (e) {
      walletBalStatus.textContent = "Error: " + e.message;
      balanceAmount.textContent = "—";
      showToast("Wallet fetch failed: " + e.message, true);
    });
  }

  // ── transactions ──
  function refreshTx() {
    txList.innerHTML = '<div class="empty">Loading…</div>';
    apiGet("/api/transactions").then(function (txs) {
      renderTxList(Array.isArray(txs) ? txs : [txs]);
    }).catch(function (e) {
      txList.innerHTML = '<div class="empty">Unavailable</div>';
    });
  }

  function renderTxList(txs) {
    if (!txs || !txs.length) {
      txList.innerHTML = '<div class="empty">No transactions.</div>';
      return;
    }
    txList.innerHTML = txs.slice(0, 5).map(function (tx) {
      var date = tx.timestamp || tx.createdAt || "";
      return '<div class="list-item">' +
        '<div class="list-top">' +
          '<span class="list-title">' +
            (tx.from ? escapeHtml(fmtAddr(tx.from)) + " → " : "") +
            (tx.to ? escapeHtml(fmtAddr(tx.to)) : "") +
          '</span>' +
          '<span class="badge">' + escapeHtml(tx.status || "unknown") + '</span>' +
        '</div>' +
        '<div class="meta">' +
          (tx.amount ? escapeHtml(tx.amount + " " + (tx.tokenSymbol || "USDC")) + " · " : "") +
          (tx.txHash ? escapeHtml("tx: " + fmtAddr(tx.txHash)) + " · " : "") +
          escapeHtml(date) +
        '</div>' +
      '</div>';
    }).join("");
  }

  // ── network ──
  function refreshNetwork() {
    networkInfo.innerHTML = '<div class="empty">Loading…</div>';
    apiGet("/api/network").then(function (n) {
      networkInfo.innerHTML =
        '<dl class="detail-list">' +
          '<div class="detail-row"><dt>Network</dt><dd>' + escapeHtml(n.network) + '</dd></div>' +
          '<div class="detail-row"><dt>Chain ID</dt><dd>' + n.chain_id + '</dd></div>' +
          '<div class="detail-row"><dt>RPC</dt><dd class="mono">' + escapeHtml(n.rpc_url) + '</dd></div>' +
          '<div class="detail-row"><dt>Explorer</dt><dd><a href="' + escapeHtml(n.explorer) + '" rel="noopener noreferrer">' + escapeHtml(n.explorer) + '</a></dd></div>' +
          '<div class="detail-row"><dt>Wallet</dt><dd class="mono">' + escapeHtml(fmtAddr(n.circle_wallet)) + '</dd></div>' +
          '<div class="detail-row"><dt>USDC Token</dt><dd class="mono">' + escapeHtml(fmtAddr(n.usdc_token)) + '</dd></div>' +
        '</dl>';
    }).catch(function () {
      networkInfo.innerHTML = '<div class="empty">Unavailable.</div>';
    });
  }

  // ── intents ──
  function refreshIntents() {
    apiGet("/api/intents").then(function (intents) {
      renderIntents(Array.isArray(intents) ? intents : []);
    }).catch(function () {
      intentList.innerHTML = '<div class="empty">Unavailable.</div>';
    });
  }

  function renderIntents(intents) {
    if (!intents || !intents.length) {
      intentList.innerHTML = '<div class="empty">No payment intents yet.</div>';
      return;
    }
    intentList.innerHTML = intents.map(function (i) {
      var badge = badgeClass(i.status);
      var estimateBlock = "";
      if (i.estimate) {
        estimateBlock = '<div class="estimate">' +
          '<strong>Estimate:</strong> ' + escapeHtml(JSON.stringify(i.estimate)) +
        '</div>';
      }
      return '<div class="list-item">' +
        '<div class="list-top">' +
          '<span class="list-title">' + escapeHtml(i.agent || "Unknown") + ' — ' + escapeHtml(i.amount || "0") + ' USDC</span>' +
          '<span class="badge ' + badge + '">' + escapeHtml(i.status || "unknown") + '</span>' +
        '</div>' +
        '<div class="meta">' +
          'ID: ' + escapeHtml(i.id) + ' · To: ' + escapeHtml(fmtAddr(i.recipient)) +
          (i.memo ? ' · ' + escapeHtml(i.memo.slice(0, 60)) : '') +
          (i.created_at ? ' · Created: ' + escapeHtml(i.created_at) : '') +
        '</div>' +
        estimateBlock +
      '</div>';
    }).join("");
  }

  // ── create intent ──
  function handleCreateIntent(e) {
    e.preventDefault();
    var agent = $("#agent").value.trim() || "Payment Agent";
    var amount = $("#amount").value.trim();
    var recipient = $("#recipient").value.trim();
    var memo = $("#memo").value.trim();

    if (!recipient || !amount) {
      showToast("Recipient and amount are required.", true);
      return;
    }

    hideToast();
    var btn = intentForm.querySelector("button[type=submit]");
    var origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Creating…";

    apiPost("/api/intent", {
      agent: agent,
      amount: amount,
      recipient: recipient,
      memo: memo,
      asset: "USDC",
    }).then(function (intent) {
      showToast("Intent created: " + intent.id);
      refreshIntents();
      btn.disabled = false;
      btn.textContent = origText;
    }).catch(function (e) {
      showToast("Error: " + e.message, true);
      btn.disabled = false;
      btn.textContent = origText;
    });
  }

  // ── refresh all ──
  function refreshAll() {
    refreshWallet();
    refreshNetwork();
    refreshTx();
    refreshIntents();
  }

  // ── init ──
  intentForm.addEventListener("submit", handleCreateIntent);
  refreshBtn.addEventListener("click", refreshAll);

  refreshAll();
})();

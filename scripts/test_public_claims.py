#!/usr/bin/env python3
"""Keep public wallet/send claims aligned with the guarded Arc Testnet scope."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = {
    "README.md": (
        "separate disabled-by-default Arc Testnet lab",
        "Custody, mainnet, autonomous spending, and live settlement remain blocked",
    ),
    "docs/contest-demo-script.md": (
        "Separate disabled-by-default Arc Testnet browser-wallet lab",
        "No wallet request on page load or from local-only demos.",
    ),
    "docs/content-pack.md": (
        "The separate guarded Arc Testnet lab permits only one manually reviewed browser-wallet transaction.",
        "No mainnet, autonomous spending, or live settlement.",
    ),
    "docs/payment-intent-quickstart.md": (
        "The separate guarded Arc Testnet send lab is outside this quickstart.",
        "What is intentionally not included in this playground",
    ),
    "docs/public-launch-packet.md": (
        "separate disabled-by-default Arc Testnet wallet-send lab",
        "No wallet request on page load or from local-only demos.",
    ),
    "docs/wallet-preflight-contract.md": (
        "A separate disabled-by-default Arc Testnet lab implements the narrow reviewed send slice",
        "Custody, mainnet, autonomous spending, and live settlement remain future work",
    ),
}

FORBIDDEN_STALE_CLAIMS = (
    "no wallet/keys/broadcast yet",
    "no wallet, no private keys, no broadcast today",
    "no wallet. no keys. no custody. no broadcast.",
    "next: guarded arc testnet status/signing",
    "real wallet permission requests, signing, and transaction submission remain future work",
    "wallet/signing/broadcast work kept behind separate future review gates",
    "no wallet connection today",
    "wallet/signing is blocked until a separate guarded testnet integration",
)


def main() -> int:
    for relative, markers in REQUIRED_MARKERS.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                raise AssertionError(f"{relative} missing public-claim marker: {marker}")

        lowered = text.lower()
        for claim in FORBIDDEN_STALE_CLAIMS:
            if claim in lowered:
                raise AssertionError(f"{relative} contains stale public claim: {claim}")

    print(f"public claims tests passed ({len(REQUIRED_MARKERS)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

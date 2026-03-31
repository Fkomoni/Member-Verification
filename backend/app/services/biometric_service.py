"""
Biometric matching service — Futronic FS80H / ftrAnakeySDK integration.

Template matching runs server-side so that stored templates never leave
the backend. The flow:

  1. Frontend captures fingerprint via Scanner Agent → gets base64 template
  2. Frontend sends template to backend API
  3. This service decrypts the stored template and calls ftrAnakeySDK
     to compare minutiae
  4. Returns match/no-match

For environments where the Futronic SDK DLLs are not available (e.g.,
CI, dev on macOS/Linux), the service falls back to a byte-comparison
stub. Set FUTRONIC_SDK_AVAILABLE=false in .env to force fallback mode.
"""

import base64
import ctypes
import hashlib
import hmac
import logging
import os
import sys

from app.core.security import decrypt_biometric_template, encrypt_biometric_template

log = logging.getLogger(__name__)

# ── Futronic SDK availability ────────────────────────────────────────
_sdk_available = False
_anakey_sdk = None

# Match threshold for 1:1 verification (0-10000, higher = stricter)
# Recommended by Futronic: 800 for standard verification
MATCH_THRESHOLD = int(os.getenv("FUTRONIC_MATCH_THRESHOLD", "800"))


def _try_load_futronic_sdk():
    """Attempt to load ftrAnakeySDK for server-side template matching."""
    global _sdk_available, _anakey_sdk

    if os.getenv("FUTRONIC_SDK_AVAILABLE", "true").lower() == "false":
        log.info("Futronic SDK disabled by config — using fallback matching")
        return

    if sys.platform != "win32":
        log.info("Futronic SDK requires Windows — using fallback matching")
        return

    try:
        search_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "scanner-agent"),
            r"C:\Program Files\Futronic\SDK\Bin",
            r"C:\Program Files (x86)\Futronic\SDK\Bin",
        ]
        for path in search_paths:
            dll_path = os.path.join(path, "ftrAnakeySDK.dll")
            if os.path.exists(dll_path):
                _anakey_sdk = ctypes.windll.LoadLibrary(dll_path)
                _sdk_available = True
                log.info("Futronic ftrAnakeySDK loaded from %s", path)
                return

        log.warning("ftrAnakeySDK.dll not found — using fallback matching")
    except Exception as e:
        log.warning("Failed to load ftrAnakeySDK: %s — using fallback matching", e)


# Load on module import
_try_load_futronic_sdk()


def encrypt_template(raw_template_b64: str) -> bytes:
    """Encrypt a base64-encoded fingerprint template for storage."""
    template_bytes = base64.b64decode(raw_template_b64)
    return encrypt_biometric_template(template_bytes)


def decrypt_template(encrypted_template: bytes) -> bytes:
    """Decrypt a stored fingerprint template."""
    return decrypt_biometric_template(encrypted_template)


def compare_templates(live_template_b64: str, stored_encrypted: bytes) -> bool:
    """
    Compare a live fingerprint scan against a stored encrypted template.

    Uses ftrAnakeySDK.AnakeyVerify() when available, otherwise falls back
    to a cryptographic byte comparison (suitable only for testing).
    """
    live_bytes = base64.b64decode(live_template_b64)
    stored_bytes = decrypt_biometric_template(stored_encrypted)

    if _sdk_available and _anakey_sdk is not None:
        return _futronic_match(live_bytes, stored_bytes)
    else:
        return _fallback_match(live_bytes, stored_bytes)


def _futronic_match(template1: bytes, template2: bytes) -> bool:
    """
    Match two ANSI 378 minutiae templates using Futronic ftrAnakeySDK.

    AnakeyVerify returns a score from 0-10000. A score >= MATCH_THRESHOLD
    indicates the same finger.
    """
    score = ctypes.c_int(0)

    result = _anakey_sdk.AnakeyVerify(
        ctypes.c_void_p(None),           # default context
        template1,                        # probe template
        ctypes.c_int(len(template1)),
        template2,                        # gallery template
        ctypes.c_int(len(template2)),
        ctypes.byref(score),
    )

    if result != 0:
        log.error("AnakeyVerify failed with error code %d", result)
        return False

    matched = score.value >= MATCH_THRESHOLD
    log.info(
        "Futronic match: score=%d threshold=%d result=%s",
        score.value,
        MATCH_THRESHOLD,
        "MATCH" if matched else "NO_MATCH",
    )
    return matched


def _fallback_match(template1: bytes, template2: bytes) -> bool:
    """
    Fallback: constant-time byte comparison for dev/test environments
    where the Futronic SDK is not installed.

    WARNING: This is NOT real fingerprint matching. It only returns True
    if the exact same template bytes are provided. Replace with SDK in
    production.
    """
    log.warning("Using fallback byte-comparison (not real biometric matching)")
    return hmac.compare_digest(
        hashlib.sha256(template1).digest(),
        hashlib.sha256(template2).digest(),
    )

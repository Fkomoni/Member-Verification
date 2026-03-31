"""
Biometric matching service.

This module wraps the fingerprint SDK interaction. In production, replace
the `_compare_templates` function with the actual vendor SDK call
(e.g., SecuGen, DigitalPersona, Futronic).
"""

import base64
import hashlib
import hmac

from backend.app.core.security import decrypt_biometric_template, encrypt_biometric_template


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

    In production, this calls the fingerprint vendor SDK's matching function
    (e.g., SecuGen's SGFPM.MatchTemplate or DigitalPersona's DP.Compare).

    For now, this performs a cryptographic comparison of the raw bytes.
    Replace the body of this function with your SDK integration.
    """
    live_bytes = base64.b64decode(live_template_b64)
    stored_bytes = decrypt_biometric_template(stored_encrypted)

    # --- VENDOR SDK INTEGRATION POINT ---
    # Replace the comparison below with:
    #   score = sdk.match_templates(live_bytes, stored_bytes)
    #   return score >= MATCH_THRESHOLD
    #
    # For demo/testing, we do a constant-time byte comparison.
    # Real fingerprint matching uses minutiae-based scoring.
    return hmac.compare_digest(
        hashlib.sha256(live_bytes).digest(),
        hashlib.sha256(stored_bytes).digest(),
    )

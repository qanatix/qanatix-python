"""Webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify a Qanatix webhook signature.

    Args:
        payload: Raw request body bytes.
        signature: Value of the X-Qanatix-Signature header.
        secret: Your webhook signing secret.

    Returns:
        True if the signature is valid.
    """
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

"""Qanatix SDK errors."""

from __future__ import annotations


class QanatixError(Exception):
    """Base exception for all Qanatix SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}

    def __repr__(self) -> str:
        if self.status_code:
            return f"QanatixError({self.status_code}: {self})"
        return f"QanatixError({self})"


class AuthenticationError(QanatixError):
    """Raised on 401 — invalid or missing API key."""


class PermissionError(QanatixError):
    """Raised on 403 — insufficient scopes."""


class NotFoundError(QanatixError):
    """Raised on 404 — resource does not exist."""


class ValidationError(QanatixError):
    """Raised on 422 — request body failed validation."""


class RateLimitError(QanatixError):
    """Raised on 429 — too many requests."""

    def __init__(self, message: str, retry_after: float | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(QanatixError):
    """Raised on 5xx — server-side error."""


def _raise_for_status(response) -> None:
    """Raise a typed error from an httpx response."""
    if response.status_code < 400:
        return

    try:
        body = response.json()
    except Exception:
        body = {}

    message = body.get("detail") or body.get("message") or response.text or f"HTTP {response.status_code}"
    code = response.status_code

    if code == 401:
        raise AuthenticationError(message, status_code=code, body=body)
    if code == 403:
        raise PermissionError(message, status_code=code, body=body)
    if code == 404:
        raise NotFoundError(message, status_code=code, body=body)
    if code == 422:
        raise ValidationError(message, status_code=code, body=body)
    if code == 429:
        retry_after = response.headers.get("retry-after")
        raise RateLimitError(
            message,
            status_code=code,
            body=body,
            retry_after=float(retry_after) if retry_after else None,
        )
    if code >= 500:
        raise ServerError(message, status_code=code, body=body)
    raise QanatixError(message, status_code=code, body=body)

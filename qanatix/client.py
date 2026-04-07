"""HTTP client with retry, auth, and namespace wiring."""

from __future__ import annotations

import time
from typing import Any

import httpx

from .errors import _raise_for_status, RateLimitError

_DEFAULT_BASE_URL = "https://api.qanatix.com"
_DEFAULT_API_PREFIX = "/api/v1"
_OPEN_API_PREFIX = "/open/v1"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_RETRYABLE_STATUS = {429, 502, 503, 504}
_CHUNK_SIZE = 5000


def _backoff(attempt: int, retry_after: float | None = None) -> float:
    if retry_after and retry_after > 0:
        return retry_after
    return min(2 ** attempt, 8)


class _SyncHTTP:
    """Synchronous HTTP transport with retry."""

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        timeout: float,
        api_prefix: str = _DEFAULT_API_PREFIX,
        extra_headers: dict[str, str] | None = None,
    ):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "qanatix-python/0.1.0",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        self.api_prefix = api_prefix

    def request(self, method: str, path: str, **kwargs) -> Any:
        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self._client.request(method, path, **kwargs)
                if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    retry_after = resp.headers.get("retry-after")
                    time.sleep(_backoff(attempt, float(retry_after) if retry_after else None))
                    continue
                _raise_for_status(resp)
                if resp.status_code == 204:
                    return None
                return resp.json()
            except RateLimitError as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_backoff(attempt, e.retry_after))
                    continue
                raise
            except httpx.TransportError as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_backoff(attempt))
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    def upload(self, path: str, file_data: bytes, filename: str, content_type: str = "text/csv") -> Any:
        """Multipart file upload."""
        resp = self._client.post(
            path,
            files={"file": (filename, file_data, content_type)},
            headers={"Content-Type": None},  # let httpx set multipart boundary
        )
        _raise_for_status(resp)
        return resp.json()

    def stream_get(self, path: str, **kwargs):
        """Return raw response for streaming (export)."""
        resp = self._client.send(
            self._client.build_request("GET", path, **kwargs),
            stream=True,
        )
        _raise_for_status(resp)
        return resp

    def close(self):
        self._client.close()


class _AsyncHTTP:
    """Async HTTP transport with retry."""

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        timeout: float,
        api_prefix: str = _DEFAULT_API_PREFIX,
        extra_headers: dict[str, str] | None = None,
    ):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "qanatix-python/0.1.0",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        self.api_prefix = api_prefix

    async def request(self, method: str, path: str, **kwargs) -> Any:
        import asyncio
        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.request(method, path, **kwargs)
                if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    retry_after = resp.headers.get("retry-after")
                    await asyncio.sleep(_backoff(attempt, float(retry_after) if retry_after else None))
                    continue
                _raise_for_status(resp)
                if resp.status_code == 204:
                    return None
                return resp.json()
            except RateLimitError as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_backoff(attempt, e.retry_after))
                    continue
                raise
            except httpx.TransportError as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    async def upload(self, path: str, file_data: bytes, filename: str, content_type: str = "text/csv") -> Any:
        resp = await self._client.post(
            path,
            files={"file": (filename, file_data, content_type)},
            headers={"Content-Type": None},
        )
        _raise_for_status(resp)
        return resp.json()

    async def close(self):
        await self._client.aclose()


CHUNK_SIZE = _CHUNK_SIZE

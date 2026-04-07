"""Qanatix Python SDK."""

from __future__ import annotations

from typing import Any

from .client import _SyncHTTP, _AsyncHTTP, _DEFAULT_BASE_URL, _DEFAULT_TIMEOUT, _DEFAULT_API_PREFIX, _OPEN_API_PREFIX
from .records import Records, AsyncRecords
from .ingest import Ingest, AsyncIngest
from .search import Search, AsyncSearch
from .connectors import Connectors, AsyncConnectors
from .collections import Collections, AsyncCollections
from .keys import Keys, AsyncKeys
from .webhooks import verify_signature
from .webhooks_resource import WebhooksMgmt, AsyncWebhooksMgmt
from .errors import (
    QanatixError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)
from .types import (
    Record,
    SearchResult,
    SearchResponse,
    Pagination,
    IngestionResult,
    UploadSummary,
    UploadError,
    CollectionInfo,
    ApiKey,
    Connector,
    WebhookSubscription,
)

__version__ = "1.0.0"

__all__ = [
    "Qanatix",
    "AsyncQanatix",
    "QanatixOpen",
    "AsyncQanatixOpen",
    "QanatixError",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "verify_signature",
    "Record",
    "SearchResult",
    "SearchResponse",
    "Pagination",
    "IngestionResult",
    "UploadSummary",
    "UploadError",
    "CollectionInfo",
    "ApiKey",
    "Connector",
    "WebhookSubscription",
]


# ── Private API (requires API key) ──


class Qanatix:
    """Synchronous Qanatix client for private data.

    Usage::

        import qanatix

        qx = qanatix.Qanatix("sk_live_...")
        results = qx.search("my_collection", "search query")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self._http = _SyncHTTP(api_key, base_url, timeout, _DEFAULT_API_PREFIX)
        self.records = Records(self._http)
        self.ingest = Ingest(self._http)
        self.search = Search(self._http)
        self.connectors = Connectors(self._http)
        self.collections = Collections(self._http)
        self.keys = Keys(self._http)
        self.webhooks = WebhooksMgmt(self._http)

    def chat(self, message: str, *, history: list[dict] | None = None) -> str:
        """Ask a question about your data in natural language.

        Qanatix uses AI to query your collections — writes SQL, executes it,
        and returns a formatted answer. Counts as 1 search.

        Args:
            message: Your question (e.g. "Show me ETFs with fees under 0.1%")
            history: Optional conversation history [{role, content}, ...]

        Returns:
            The assistant's response as a string (markdown formatted).
        """
        resp = self._http.request("POST", f"{self._http.api_prefix}/chat", json={
            "message": message,
            "history": history or [],
        })
        if isinstance(resp, dict):
            if resp.get("error"):
                from .errors import QanatixError
                raise QanatixError(resp["error"], status_code=resp.get("status"))
            return resp.get("response", "")
        return str(resp)

    def export(self, collection: str, *, format: str = "json") -> Any:
        """Stream export of a collection."""
        return self._http.stream_get(
            f"{self._http.api_prefix}/export", params={"collection": collection, "format": format},
        )

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncQanatix:
    """Async Qanatix client for private data.

    Usage::

        import qanatix

        async with qanatix.AsyncQanatix("sk_live_...") as qx:
            results = await qx.search("my_collection", "search query")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self._http = _AsyncHTTP(api_key, base_url, timeout, _DEFAULT_API_PREFIX)
        self.records = AsyncRecords(self._http)
        self.ingest = AsyncIngest(self._http)
        self.search = AsyncSearch(self._http)
        self.connectors = AsyncConnectors(self._http)
        self.collections = AsyncCollections(self._http)
        self.keys = AsyncKeys(self._http)
        self.webhooks = AsyncWebhooksMgmt(self._http)

    async def chat(self, message: str, *, history: list[dict] | None = None) -> str:
        """Ask a question about your data. See Qanatix.chat() for details."""
        resp = await self._http.request("POST", f"{self._http.api_prefix}/chat", json={
            "message": message,
            "history": history or [],
        })
        if isinstance(resp, dict):
            if resp.get("error"):
                from .errors import QanatixError
                raise QanatixError(resp["error"], status_code=resp.get("status"))
            return resp.get("response", "")
        return str(resp)

    async def export(self, collection: str, *, format: str = "json") -> Any:
        """Export is not yet supported in async mode. Use sync client."""
        raise NotImplementedError("Use the sync Qanatix client for exports")

    async def close(self):
        await self._http.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# ── Open API (no auth, read-only) ──


class QanatixOpen:
    """Synchronous client for Qanatix Open — public data, no API key needed.

    Usage::

        import qanatix

        qx = qanatix.QanatixOpen()
        results = qx.search("us-spending", "NASA renewable energy")
        collections = qx.collections.list()
    """

    def __init__(
        self,
        *,
        agent_id: str | None = None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        extra_headers = {"X-Agent-Id": agent_id} if agent_id else None
        self._http = _SyncHTTP(None, base_url, timeout, _OPEN_API_PREFIX, extra_headers=extra_headers)
        self.search = Search(self._http)
        self.collections = Collections(self._http)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncQanatixOpen:
    """Async client for Qanatix Open — public data, no API key needed.

    Usage::

        import qanatix

        async with qanatix.AsyncQanatixOpen() as qx:
            results = await qx.search("us-spending", "NASA renewable energy")
    """

    def __init__(
        self,
        *,
        agent_id: str | None = None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        extra_headers = {"X-Agent-Id": agent_id} if agent_id else None
        self._http = _AsyncHTTP(None, base_url, timeout, _OPEN_API_PREFIX, extra_headers=extra_headers)
        self.search = AsyncSearch(self._http)
        self.collections = AsyncCollections(self._http)

    async def close(self):
        await self._http.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

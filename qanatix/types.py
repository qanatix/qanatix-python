"""Qanatix SDK data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Record:
    record_id: str
    name: str
    collection: str
    record_type: str
    data: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    description_llm: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    source_id: str | None = None
    status: str = "active"
    visibility: str = "private"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class SearchResult:
    record_id: str
    name: str
    score: float
    collection: str
    record_type: str
    collection_data: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    description_llm: str | None = None
    source_type: str | None = None
    updated_at: str | None = None


@dataclass
class SearchResponse:
    results: list[SearchResult]
    pagination: Pagination
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Pagination:
    offset: int
    limit: int
    has_more: bool


@dataclass
class UploadSummary:
    submitted: int = 0
    accepted: int = 0
    rejected: int = 0
    dedup_skipped: int = 0


@dataclass
class UploadError:
    row: int | None = None
    field: str | None = None
    error_type: str | None = None
    message: str = ""


@dataclass
class IngestionResult:
    upload_id: str
    status: str
    summary: UploadSummary
    errors: list[UploadError] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    _client: Any = field(default=None, repr=False)

    def wait(self, poll_interval: float = 1.0, timeout: float = 300.0) -> "IngestionResult":
        """Poll until upload completes. Sync only."""
        if self._client is None:
            raise RuntimeError("Cannot poll without a client reference")
        import time
        elapsed = 0.0
        while self.status not in ("complete", "failed") and elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval
            result = self._client._get(f"/uploads/{self.upload_id}")
            self.status = result.get("status", self.status)
        return self

    async def async_wait(self, poll_interval: float = 1.0, timeout: float = 300.0) -> "IngestionResult":
        """Poll until upload completes. Async only."""
        if self._client is None:
            raise RuntimeError("Cannot poll without a client reference")
        import asyncio
        elapsed = 0.0
        while self.status not in ("complete", "failed") and elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            result = await self._client._get(f"/uploads/{self.upload_id}")
            self.status = result.get("status", self.status)
        return self


@dataclass
class CollectionInfo:
    collection: str
    description: str | None = None
    category: str | None = None
    record_types: list[str] = field(default_factory=list)
    record_count: int = 0
    has_schema: bool = False


@dataclass
class ApiKey:
    id: str
    name: str
    key: str | None = None
    scopes: list[str] = field(default_factory=list)
    expires_at: str | None = None
    created_at: str | None = None


@dataclass
class Connector:
    id: str
    name: str
    connector_type: str
    collection: str
    record_type: str
    status: str = "active"


@dataclass
class Schema:
    collection: str
    record_type: str
    json_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookSubscription:
    id: str
    url: str
    events: list[str] = field(default_factory=list)
    secret: str | None = None
    active: bool = True
    description: str | None = None
    created_at: str | None = None


@dataclass
class Member:
    id: str
    email: str
    full_name: str | None = None
    role: str = "member"
    created_at: str | None = None


@dataclass
class Invite:
    id: str
    email: str
    role: str = "member"
    expires_at: str | None = None
    created_at: str | None = None


@dataclass
class AuditEntry:
    id: str
    actor_email: str | None = None
    action: str = ""
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    created_at: str | None = None


@dataclass
class AuditPage:
    entries: list[AuditEntry] = field(default_factory=list)
    total: int = 0
    page: int = 1
    pages: int = 1

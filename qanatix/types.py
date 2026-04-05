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
class WebhookSubscription:
    id: str
    url: str
    events: list[str] = field(default_factory=list)
    secret: str | None = None
    active: bool = True
    description: str | None = None
    created_at: str | None = None

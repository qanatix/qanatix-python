"""Search resource — query + auto-paginating iterator."""

from __future__ import annotations

from typing import Any, Iterator, AsyncIterator

from .types import SearchResult, SearchResponse, Pagination


def _to_result(data: dict) -> SearchResult:
    return SearchResult(
        record_id=data.get("record_id", ""),
        name=data.get("name", ""),
        score=data.get("score", 0.0),
        collection=data.get("collection", ""),
        record_type=data.get("record_type", ""),
        collection_data=data.get("collection_data", data.get("data", {})),
        description=data.get("description"),
        description_llm=data.get("description_llm"),
        source_type=data.get("source_type"),
        updated_at=data.get("updated_at"),
    )


def _to_response(data: dict) -> SearchResponse:
    pag = data.get("pagination", {})
    return SearchResponse(
        results=[_to_result(r) for r in data.get("results", [])],
        pagination=Pagination(
            offset=pag.get("offset", 0),
            limit=pag.get("limit", 20),
            has_more=pag.get("has_more", False),
        ),
        metadata=data.get("metadata", {}),
    )


class Search:
    """Synchronous search — callable + .iter() for auto-pagination."""

    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/search"

    def __call__(
        self,
        collection: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        format: str = "json",
    ) -> SearchResponse:
        body: dict[str, Any] = {"query": query, "limit": limit, "offset": offset, "format": format}
        if filters:
            body["filters"] = filters
        if sort:
            body["sort"] = sort
        return _to_response(self._http.request("POST", f"{self._api}/{collection}", json=body))

    def iter(
        self,
        collection: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        page_size: int = 20,
        sort: str | None = None,
        max_results: int | None = None,
    ) -> Iterator[SearchResult]:
        """Auto-paginate through all search results."""
        offset = 0
        yielded = 0
        while True:
            resp = self(collection, query, filters=filters, limit=page_size, offset=offset, sort=sort)
            for r in resp.results:
                yield r
                yielded += 1
                if max_results and yielded >= max_results:
                    return
            if not resp.pagination.has_more:
                return
            offset += page_size


class AsyncSearch:
    """Async search — callable + .iter() for auto-pagination."""

    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/search"

    async def __call__(
        self,
        collection: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str | None = None,
        format: str = "json",
    ) -> SearchResponse:
        body: dict[str, Any] = {"query": query, "limit": limit, "offset": offset, "format": format}
        if filters:
            body["filters"] = filters
        if sort:
            body["sort"] = sort
        return _to_response(await self._http.request("POST", f"{self._api}/{collection}", json=body))

    async def iter(
        self,
        collection: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        page_size: int = 20,
        sort: str | None = None,
        max_results: int | None = None,
    ) -> AsyncIterator[SearchResult]:
        offset = 0
        yielded = 0
        while True:
            resp = await self(collection, query, filters=filters, limit=page_size, offset=offset, sort=sort)
            for r in resp.results:
                yield r
                yielded += 1
                if max_results and yielded >= max_results:
                    return
            if not resp.pagination.has_more:
                return
            offset += page_size

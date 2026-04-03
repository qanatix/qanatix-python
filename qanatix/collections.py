"""Collections resource — list and update."""

from __future__ import annotations

from typing import Any

from .types import CollectionInfo


def _to_collection(data: dict) -> CollectionInfo:
    return CollectionInfo(
        collection=data.get("collection", ""),
        description=data.get("description"),
        category=data.get("category"),
        record_types=data.get("record_types", []),
        record_count=data.get("record_count", 0),
        has_schema=data.get("has_schema", False),
    )


class Collections:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/collections"

    def list(self) -> list[CollectionInfo]:
        resp = self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("collections", [])
        return [_to_collection(c) for c in items]

    def update(self, collection: str, **fields) -> dict[str, Any]:
        return self._http.request("PATCH", f"{self._api}/{collection}", json=fields)


class AsyncCollections:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/collections"

    async def list(self) -> list[CollectionInfo]:
        resp = await self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("collections", [])
        return [_to_collection(c) for c in items]

    async def update(self, collection: str, **fields) -> dict[str, Any]:
        return await self._http.request("PATCH", f"{self._api}/{collection}", json=fields)

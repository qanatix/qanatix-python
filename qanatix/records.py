"""Records resource — CRUD + bulk operations."""

from __future__ import annotations

from typing import Any

from .types import Record


def _to_record(data: dict) -> Record:
    return Record(
        record_id=data.get("id", data.get("record_id", "")),
        name=data.get("name", ""),
        collection=data.get("collection", ""),
        record_type=data.get("record_type", ""),
        data=data.get("data", {}),
        description=data.get("description"),
        description_llm=data.get("description_llm"),
        source_type=data.get("source_type"),
        source_url=data.get("source_url"),
        source_id=data.get("source_id"),
        status=data.get("status", "active"),
        visibility=data.get("visibility", "private"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


class Records:
    """Synchronous records resource."""

    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/records"

    def create(
        self,
        collection: str,
        record_type: str,
        name: str,
        data: dict[str, Any] | None = None,
        *,
        description: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        visibility: str = "private",
    ) -> Record:
        body: dict[str, Any] = {
            "collection": collection,
            "record_type": record_type,
            "name": name,
        }
        if data:
            body["data"] = data
        if description:
            body["description"] = description
        if source_type:
            body["source_type"] = source_type
        if source_id:
            body["source_id"] = source_id
        if visibility != "private":
            body["visibility"] = visibility
        return _to_record(self._http.request("POST", self._api, json=body))

    def get(self, record_id: str) -> Record:
        return _to_record(self._http.request("GET", f"{self._api}/{record_id}"))

    def list(self, *, cursor: str | None = None, limit: int = 20) -> list[Record]:
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self._http.request("GET", self._api, params=params)
        items = resp if isinstance(resp, list) else resp.get("records", resp.get("results", []))
        return [_to_record(r) for r in items]

    def update(self, record_id: str, **fields) -> Record:
        return _to_record(self._http.request("PATCH", f"{self._api}/{record_id}", json=fields))

    def delete(self, record_id: str) -> None:
        self._http.request("DELETE", f"{self._api}/{record_id}")

    def bulk_update(self, record_ids: list[str], **fields) -> list[Record]:
        body = {"record_ids": record_ids, **fields}
        resp = self._http.request("PATCH", f"{self._api}/bulk", json=body)
        items = resp if isinstance(resp, list) else resp.get("records", [])
        return [_to_record(r) for r in items]

    def bulk_delete(self, record_ids: list[str]) -> int:
        resp = self._http.request("POST", f"{self._api}/bulk-delete", json={"record_ids": record_ids})
        return resp.get("archived", 0) if isinstance(resp, dict) else 0


class AsyncRecords:
    """Async records resource."""

    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/records"

    async def create(
        self,
        collection: str,
        record_type: str,
        name: str,
        data: dict[str, Any] | None = None,
        *,
        description: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        visibility: str = "private",
    ) -> Record:
        body: dict[str, Any] = {
            "collection": collection,
            "record_type": record_type,
            "name": name,
        }
        if data:
            body["data"] = data
        if description:
            body["description"] = description
        if source_type:
            body["source_type"] = source_type
        if source_id:
            body["source_id"] = source_id
        if visibility != "private":
            body["visibility"] = visibility
        return _to_record(await self._http.request("POST", self._api, json=body))

    async def get(self, record_id: str) -> Record:
        return _to_record(await self._http.request("GET", f"{self._api}/{record_id}"))

    async def list(self, *, cursor: str | None = None, limit: int = 20) -> list[Record]:
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = await self._http.request("GET", self._api, params=params)
        items = resp if isinstance(resp, list) else resp.get("records", resp.get("results", []))
        return [_to_record(r) for r in items]

    async def update(self, record_id: str, **fields) -> Record:
        return _to_record(await self._http.request("PATCH", f"{self._api}/{record_id}", json=fields))

    async def delete(self, record_id: str) -> None:
        await self._http.request("DELETE", f"{self._api}/{record_id}")

    async def bulk_update(self, record_ids: list[str], **fields) -> list[Record]:
        body = {"record_ids": record_ids, **fields}
        resp = await self._http.request("PATCH", f"{self._api}/bulk", json=body)
        items = resp if isinstance(resp, list) else resp.get("records", [])
        return [_to_record(r) for r in items]

    async def bulk_delete(self, record_ids: list[str]) -> int:
        resp = await self._http.request("POST", f"{self._api}/bulk-delete", json={"record_ids": record_ids})
        return resp.get("archived", 0) if isinstance(resp, dict) else 0

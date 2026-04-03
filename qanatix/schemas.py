"""Schemas resource — register and retrieve JSON Schemas."""

from __future__ import annotations

from typing import Any

from .types import Schema


def _to_schema(data: dict) -> Schema:
    return Schema(
        collection=data.get("collection", ""),
        record_type=data.get("record_type", ""),
        json_schema=data.get("json_schema", {}),
    )


class Schemas:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/schemas"

    def register(self, collection: str, record_type: str, json_schema: dict[str, Any]) -> Schema:
        data = self._http.request("POST", self._api, json={
            "collection": collection,
            "record_type": record_type,
            "json_schema": json_schema,
        })
        return _to_schema(data)

    def list(self, *, collection: str | None = None) -> list[Schema]:
        params = {}
        if collection:
            params["collection"] = collection
        resp = self._http.request("GET", self._api, params=params)
        items = resp if isinstance(resp, list) else resp.get("schemas", [])
        return [_to_schema(s) for s in items]

    def get(self, collection: str, record_type: str) -> Schema:
        return _to_schema(self._http.request("GET", f"{self._api}/{collection}/{record_type}"))


class AsyncSchemas:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/schemas"

    async def register(self, collection: str, record_type: str, json_schema: dict[str, Any]) -> Schema:
        data = await self._http.request("POST", self._api, json={
            "collection": collection,
            "record_type": record_type,
            "json_schema": json_schema,
        })
        return _to_schema(data)

    async def list(self, *, collection: str | None = None) -> list[Schema]:
        params = {}
        if collection:
            params["collection"] = collection
        resp = await self._http.request("GET", self._api, params=params)
        items = resp if isinstance(resp, list) else resp.get("schemas", [])
        return [_to_schema(s) for s in items]

    async def get(self, collection: str, record_type: str) -> Schema:
        return _to_schema(await self._http.request("GET", f"{self._api}/{collection}/{record_type}"))

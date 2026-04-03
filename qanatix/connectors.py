"""Connectors resource — create, list, pull, delete."""

from __future__ import annotations

from typing import Any

from .types import Connector


def _to_connector(data: dict) -> Connector:
    return Connector(
        id=data.get("id", ""),
        name=data.get("name", ""),
        connector_type=data.get("connector_type", ""),
        collection=data.get("collection", ""),
        record_type=data.get("record_type", ""),
        status=data.get("status", "active"),
    )


class Connectors:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/connectors"

    def create(
        self,
        name: str,
        connector_type: str,
        collection: str,
        record_type: str,
        connection_config: dict[str, Any],
        query: str,
        *,
        name_column: str = "name",
        schedule: str | None = None,
        batch_size: int = 1000,
    ) -> Connector:
        body: dict[str, Any] = {
            "name": name,
            "connector_type": connector_type,
            "collection": collection,
            "record_type": record_type,
            "connection_config": connection_config,
            "query": query,
            "name_column": name_column,
            "batch_size": batch_size,
        }
        if schedule:
            body["schedule"] = schedule
        return _to_connector(self._http.request("POST", self._api, json=body))

    def list(self) -> list[Connector]:
        resp = self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("connectors", [])
        return [_to_connector(c) for c in items]

    def pull(self, connector_id: str) -> dict[str, Any]:
        return self._http.request("POST", f"{self._api}/{connector_id}/pull")

    def delete(self, connector_id: str) -> None:
        self._http.request("DELETE", f"{self._api}/{connector_id}")


class AsyncConnectors:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/connectors"

    async def create(
        self,
        name: str,
        connector_type: str,
        collection: str,
        record_type: str,
        connection_config: dict[str, Any],
        query: str,
        *,
        name_column: str = "name",
        schedule: str | None = None,
        batch_size: int = 1000,
    ) -> Connector:
        body: dict[str, Any] = {
            "name": name,
            "connector_type": connector_type,
            "collection": collection,
            "record_type": record_type,
            "connection_config": connection_config,
            "query": query,
            "name_column": name_column,
            "batch_size": batch_size,
        }
        if schedule:
            body["schedule"] = schedule
        return _to_connector(await self._http.request("POST", self._api, json=body))

    async def list(self) -> list[Connector]:
        resp = await self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("connectors", [])
        return [_to_connector(c) for c in items]

    async def pull(self, connector_id: str) -> dict[str, Any]:
        return await self._http.request("POST", f"{self._api}/{connector_id}/pull")

    async def delete(self, connector_id: str) -> None:
        await self._http.request("DELETE", f"{self._api}/{connector_id}")

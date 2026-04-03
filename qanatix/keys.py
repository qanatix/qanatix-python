"""API Keys resource — create, list, revoke, rotate."""

from __future__ import annotations

from typing import Any

from .types import ApiKey


def _to_key(data: dict) -> ApiKey:
    return ApiKey(
        id=data.get("id", ""),
        name=data.get("name", ""),
        key=data.get("key"),
        scopes=data.get("scopes", []),
        expires_at=data.get("expires_at"),
        created_at=data.get("created_at"),
    )


class Keys:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/auth/keys"

    def create(self, name: str, scopes: list[str], *, expires_at: str | None = None) -> ApiKey:
        body: dict[str, Any] = {"name": name, "scopes": scopes}
        if expires_at:
            body["expires_at"] = expires_at
        return _to_key(self._http.request("POST", self._api, json=body))

    def list(self) -> list[ApiKey]:
        resp = self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("keys", [])
        return [_to_key(k) for k in items]

    def revoke(self, key_id: str) -> None:
        self._http.request("DELETE", f"{self._api}/{key_id}")

    def rotate(self, key_id: str) -> ApiKey:
        return _to_key(self._http.request("POST", f"{self._api}/{key_id}/rotate"))


class AsyncKeys:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/auth/keys"

    async def create(self, name: str, scopes: list[str], *, expires_at: str | None = None) -> ApiKey:
        body: dict[str, Any] = {"name": name, "scopes": scopes}
        if expires_at:
            body["expires_at"] = expires_at
        return _to_key(await self._http.request("POST", self._api, json=body))

    async def list(self) -> list[ApiKey]:
        resp = await self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("keys", [])
        return [_to_key(k) for k in items]

    async def revoke(self, key_id: str) -> None:
        await self._http.request("DELETE", f"{self._api}/{key_id}")

    async def rotate(self, key_id: str) -> ApiKey:
        return _to_key(await self._http.request("POST", f"{self._api}/{key_id}/rotate"))

"""Webhook subscriptions resource — create, list, delete, test, deliveries."""

from __future__ import annotations

from typing import Any

from .types import WebhookSubscription


def _to_webhook(data: dict) -> WebhookSubscription:
    return WebhookSubscription(
        id=data.get("id", ""),
        url=data.get("url", ""),
        events=data.get("events", []),
        secret=data.get("secret"),
        active=data.get("active", True),
        description=data.get("description"),
        created_at=data.get("created_at"),
    )


class WebhooksMgmt:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/portal/webhooks"

    def create(self, url: str, events: list[str], description: str | None = None) -> WebhookSubscription:
        body: dict[str, Any] = {"url": url, "events": events}
        if description:
            body["description"] = description
        return _to_webhook(self._http.request("POST", self._api, json=body))

    def list(self) -> list[WebhookSubscription]:
        resp = self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("webhooks", [])
        return [_to_webhook(w) for w in items]

    def delete(self, webhook_id: str) -> None:
        self._http.request("DELETE", f"{self._api}/{webhook_id}")

    def test(self, webhook_id: str) -> dict:
        return self._http.request("POST", f"{self._api}/{webhook_id}/test")

    def deliveries(self, webhook_id: str) -> list[dict]:
        resp = self._http.request("GET", f"{self._api}/{webhook_id}/deliveries")
        return resp if isinstance(resp, list) else resp.get("deliveries", [])


class AsyncWebhooksMgmt:
    def __init__(self, http):
        self._http = http
        self._api = f"{http.api_prefix}/portal/webhooks"

    async def create(self, url: str, events: list[str], description: str | None = None) -> WebhookSubscription:
        body: dict[str, Any] = {"url": url, "events": events}
        if description:
            body["description"] = description
        return _to_webhook(await self._http.request("POST", self._api, json=body))

    async def list(self) -> list[WebhookSubscription]:
        resp = await self._http.request("GET", self._api)
        items = resp if isinstance(resp, list) else resp.get("webhooks", [])
        return [_to_webhook(w) for w in items]

    async def delete(self, webhook_id: str) -> None:
        await self._http.request("DELETE", f"{self._api}/{webhook_id}")

    async def test(self, webhook_id: str) -> dict:
        return await self._http.request("POST", f"{self._api}/{webhook_id}/test")

    async def deliveries(self, webhook_id: str) -> list[dict]:
        resp = await self._http.request("GET", f"{self._api}/{webhook_id}/deliveries")
        return resp if isinstance(resp, list) else resp.get("deliveries", [])

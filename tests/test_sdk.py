"""Unit tests for the Qanatix Python SDK."""

from __future__ import annotations

import json
import pytest
import httpx

import qanatix
from qanatix.errors import (
    QanatixError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    ServerError,
    _raise_for_status,
)
from qanatix.types import UploadSummary, UploadError
from qanatix.webhooks import verify_signature
from qanatix.client import _backoff, CHUNK_SIZE


# ── Helpers ──

class FakeResponse:
    def __init__(self, status_code=200, data=None, headers=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._data


class FakeHTTP:
    """Mock HTTP transport that records calls and returns canned responses."""

    def __init__(self, responses=None):
        self.calls = []
        self._responses = responses or [{}]
        self._idx = 0
        self.api_prefix = "/api/v1"

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        resp = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        return resp

    def upload(self, path, file_data, filename, content_type="text/csv"):
        self.calls.append(("UPLOAD", path, {"filename": filename}))
        resp = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        return resp

    def _get(self, path):
        return self.request("GET", path)


# ── Error tests ──

class TestErrors:
    def test_401(self):
        resp = FakeResponse(401, {"detail": "Invalid API key"})
        with pytest.raises(AuthenticationError):
            _raise_for_status(resp)

    def test_404(self):
        resp = FakeResponse(404, {"detail": "Not found"})
        with pytest.raises(NotFoundError):
            _raise_for_status(resp)

    def test_422(self):
        resp = FakeResponse(422, {"detail": "Validation failed"})
        with pytest.raises(ValidationError):
            _raise_for_status(resp)

    def test_429_with_retry_after(self):
        resp = FakeResponse(429, {"detail": "Rate limited"}, headers={"retry-after": "2.5"})
        with pytest.raises(RateLimitError) as exc_info:
            _raise_for_status(resp)
        assert exc_info.value.retry_after == 2.5

    def test_500(self):
        resp = FakeResponse(500, {"detail": "Internal error"})
        with pytest.raises(ServerError):
            _raise_for_status(resp)

    def test_200_no_raise(self):
        resp = FakeResponse(200)
        _raise_for_status(resp)  # should not raise

    def test_error_repr(self):
        e = QanatixError("bad", status_code=400)
        assert "400" in repr(e)


# ── Backoff ──

class TestBackoff:
    def test_exponential(self):
        assert _backoff(0) == 1
        assert _backoff(1) == 2
        assert _backoff(2) == 4
        assert _backoff(10) == 8  # capped

    def test_retry_after_override(self):
        assert _backoff(0, retry_after=5.0) == 5.0


# ── Records ──

class TestRecords:
    def test_create(self):
        http = FakeHTTP([{
            "id": "r1", "name": "Test", "collection": "col",
            "record_type": "type", "data": {"k": "v"},
        }])
        records = qanatix.Qanatix.__new__(qanatix.Qanatix)
        records._http = http
        records.records = qanatix.records.Records(http)

        rec = records.records.create("col", "type", "Test", {"k": "v"})
        assert rec.record_id == "r1"
        assert rec.name == "Test"
        assert rec.data == {"k": "v"}
        assert http.calls[0][0] == "POST"

    def test_get(self):
        http = FakeHTTP([{
            "id": "r1", "name": "Test", "collection": "col", "record_type": "type",
        }])
        r = qanatix.records.Records(http)
        rec = r.get("r1")
        assert rec.record_id == "r1"
        assert "r1" in http.calls[0][1]

    def test_list(self):
        http = FakeHTTP([{"records": [
            {"id": "r1", "name": "A", "collection": "c", "record_type": "t"},
            {"id": "r2", "name": "B", "collection": "c", "record_type": "t"},
        ]}])
        r = qanatix.records.Records(http)
        recs = r.list(limit=10)
        assert len(recs) == 2

    def test_delete(self):
        http = FakeHTTP([None])
        r = qanatix.records.Records(http)
        r.delete("r1")
        assert http.calls[0][0] == "DELETE"

    def test_bulk_delete(self):
        http = FakeHTTP([{"archived": 3}])
        r = qanatix.records.Records(http)
        count = r.bulk_delete(["r1", "r2", "r3"])
        assert count == 3


# ── Search ──

class TestSearch:
    def test_search(self):
        http = FakeHTTP([{
            "results": [
                {"record_id": "r1", "name": "Hit", "score": 0.95, "collection": "c", "record_type": "t", "collection_data": {}},
            ],
            "pagination": {"offset": 0, "limit": 20, "has_more": False},
            "metadata": {"processing_time_ms": 12},
        }])
        s = qanatix.search.Search(http)
        resp = s("c", "test query")
        assert len(resp.results) == 1
        assert resp.results[0].score == 0.95
        assert resp.pagination.has_more is False

    def test_iter(self):
        page1 = {
            "results": [{"record_id": f"r{i}", "name": f"R{i}", "score": 0.9, "collection": "c", "record_type": "t"} for i in range(3)],
            "pagination": {"offset": 0, "limit": 3, "has_more": True},
        }
        page2 = {
            "results": [{"record_id": "r3", "name": "R3", "score": 0.8, "collection": "c", "record_type": "t"}],
            "pagination": {"offset": 3, "limit": 3, "has_more": False},
        }
        http = FakeHTTP([page1, page2])
        s = qanatix.search.Search(http)
        results = list(s.iter("c", "test", page_size=3))
        assert len(results) == 4

    def test_iter_max_results(self):
        page1 = {
            "results": [{"record_id": f"r{i}", "name": f"R{i}", "score": 0.9, "collection": "c", "record_type": "t"} for i in range(5)],
            "pagination": {"offset": 0, "limit": 5, "has_more": True},
        }
        http = FakeHTTP([page1])
        s = qanatix.search.Search(http)
        results = list(s.iter("c", "test", page_size=5, max_results=3))
        assert len(results) == 3


# ── Ingest ──

class TestIngest:
    def test_batch(self):
        http = FakeHTTP([{
            "upload_id": "u1", "status": "complete",
            "summary": {"submitted": 2, "accepted": 2, "rejected": 0},
            "errors": [],
        }])
        ing = qanatix.ingest.Ingest(http)
        result = ing.batch("col", "type", [{"name": "a"}, {"name": "b"}])
        assert result.upload_id == "u1"
        assert result.summary.accepted == 2

    def test_batch_auto_chunk(self):
        """Records > CHUNK_SIZE should be split into multiple requests."""
        records = [{"name": f"r{i}"} for i in range(CHUNK_SIZE + 100)]
        responses = [
            {"upload_id": "u1", "status": "complete", "summary": {"submitted": CHUNK_SIZE, "accepted": CHUNK_SIZE, "rejected": 0}, "errors": []},
            {"upload_id": "u2", "status": "complete", "summary": {"submitted": 100, "accepted": 100, "rejected": 0}, "errors": []},
        ]
        http = FakeHTTP(responses)
        ing = qanatix.ingest.Ingest(http)
        result = ing.batch("col", "type", records)
        assert len(http.calls) == 2
        assert result.summary.accepted == CHUNK_SIZE + 100


# ── Schemas ──

class TestSchemas:
    def test_register(self):
        http = FakeHTTP([{
            "collection": "col", "record_type": "type",
            "json_schema": {"type": "object"},
        }])
        s = qanatix.schemas.Schemas(http)
        schema = s.register("col", "type", {"type": "object"})
        assert schema.collection == "col"

    def test_list(self):
        http = FakeHTTP([{"schemas": [
            {"collection": "c1", "record_type": "t1", "json_schema": {}},
        ]}])
        s = qanatix.schemas.Schemas(http)
        schemas = s.list()
        assert len(schemas) == 1


# ── Collections ──

class TestCollections:
    def test_list(self):
        http = FakeHTTP([{"collections": [
            {"collection": "c1", "record_types": ["t1"], "record_count": 100, "has_schema": True},
        ]}])
        c = qanatix.collections.Collections(http)
        cols = c.list()
        assert len(cols) == 1
        assert cols[0].record_count == 100


# ── Keys ──

class TestKeys:
    def test_create(self):
        http = FakeHTTP([{
            "id": "k1", "name": "test-key", "key": "sk_live_abc",
            "scopes": ["search", "upload"],
        }])
        k = qanatix.keys.Keys(http)
        key = k.create("test-key", ["search", "upload"])
        assert key.key == "sk_live_abc"

    def test_revoke(self):
        http = FakeHTTP([None])
        k = qanatix.keys.Keys(http)
        k.revoke("k1")
        assert http.calls[0][0] == "DELETE"


# ── Connectors ──

class TestConnectors:
    def test_create(self):
        http = FakeHTTP([{
            "id": "cn1", "name": "pg-conn", "connector_type": "postgresql",
            "collection": "col", "record_type": "type",
        }])
        c = qanatix.connectors.Connectors(http)
        conn = c.create("pg-conn", "postgresql", "col", "type", {"host": "localhost"}, "SELECT * FROM t")
        assert conn.id == "cn1"


# ── Webhooks ──

class TestWebhooks:
    def test_verify_valid(self):
        import hmac, hashlib
        secret = "whsec_test123"
        payload = b'{"event": "record.created"}'
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert verify_signature(payload, sig, secret) is True

    def test_verify_invalid(self):
        assert verify_signature(b"payload", "bad_sig", "secret") is False


# ── Client init ──

class TestClientInit:
    def test_sync_namespaces(self):
        qx = qanatix.Qanatix.__new__(qanatix.Qanatix)
        http = FakeHTTP()
        qx._http = http
        qx.records = qanatix.records.Records(http)
        qx.search = qanatix.search.Search(http)
        qx.ingest = qanatix.ingest.Ingest(http)
        qx.schemas = qanatix.schemas.Schemas(http)
        qx.connectors = qanatix.connectors.Connectors(http)
        qx.collections = qanatix.collections.Collections(http)
        qx.keys = qanatix.keys.Keys(http)
        assert qx.records is not None
        assert qx.search is not None

    def test_version(self):
        assert qanatix.__version__ == "0.1.0"

    def test_open_client_has_search_and_collections(self):
        """QanatixOpen should only expose search + collections."""
        qx = qanatix.QanatixOpen.__new__(qanatix.QanatixOpen)
        http = FakeHTTP()
        qx._http = http
        qx.search = qanatix.search.Search(http)
        qx.collections = qanatix.collections.Collections(http)
        assert qx.search is not None
        assert qx.collections is not None
        assert not hasattr(qx, "records")
        assert not hasattr(qx, "ingest")
        assert not hasattr(qx, "keys")

    def test_open_client_no_auth_header(self):
        """QanatixOpen should not send Authorization header."""
        from qanatix.client import _SyncHTTP
        http = _SyncHTTP(None, "https://example.com", 10.0, "/open/v1")
        assert "Authorization" not in http._client.headers
        assert http.api_prefix == "/open/v1"
        http.close()

    def test_private_client_has_auth_header(self):
        """Qanatix should send Authorization header."""
        from qanatix.client import _SyncHTTP
        http = _SyncHTTP("sk_live_test", "https://example.com", 10.0)
        assert "Authorization" in http._client.headers
        assert http._client.headers["Authorization"] == "Bearer sk_live_test"
        http.close()

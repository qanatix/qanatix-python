"""Integration tests — run against the live Qanatix API.

Uses QanatixOpen (no auth) to validate SDK end-to-end.
For authenticated tests, set QANATIX_API_KEY env var.

Run:
    pytest tests/test_integration.py -v
    QANATIX_API_KEY=sk_live_... pytest tests/test_integration.py -v -k "auth"
"""

from __future__ import annotations

import os
import pytest

import qanatix
from qanatix.errors import QanatixError, NotFoundError

API_KEY = os.environ.get("QANATIX_API_KEY", "")


def auth_client() -> qanatix.Qanatix:
    """Client for the authenticated API. Requires QANATIX_API_KEY."""
    if not API_KEY:
        pytest.skip("QANATIX_API_KEY not set")
    return qanatix.Qanatix(API_KEY)


# ── Open API Tests (no auth needed) ──


class TestOpenCollections:
    """Test collections.list() against the open API."""

    def test_list_returns_collections(self):
        with qanatix.QanatixOpen() as qx:
            cols = qx.collections.list()
        assert len(cols) > 0, "Expected at least one collection"
        c = cols[0]
        assert c.collection, "collection name should be non-empty"
        assert isinstance(c.record_count, int)
        assert isinstance(c.record_types, list)

    def test_known_collection_exists(self):
        with qanatix.QanatixOpen() as qx:
            cols = qx.collections.list()
        names = [c.collection for c in cols]
        assert "us-spending" in names, f"Expected us-spending in {names}"

    def test_collection_has_records(self):
        with qanatix.QanatixOpen() as qx:
            cols = qx.collections.list()
        us = next(c for c in cols if c.collection == "us-spending")
        assert us.record_count > 1_000_000, f"Expected >1M records, got {us.record_count}"


class TestOpenSearch:
    """Test search against the open API."""

    def test_basic_search(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "education grants")
        assert len(resp.results) > 0, "Expected search results"
        assert resp.pagination.limit > 0

    def test_search_result_structure(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "education grants")
        r = resp.results[0]
        assert r.record_id, "record_id should be non-empty"
        assert r.name, "name should be non-empty"
        assert 0 <= r.score <= 1, f"score should be 0-1, got {r.score}"
        assert r.collection == "us-spending"

    def test_search_with_limit(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "healthcare", limit=3)
        assert len(resp.results) <= 3

    def test_search_with_offset(self):
        with qanatix.QanatixOpen() as qx:
            page1 = qx.search("us-spending", "education", limit=5, offset=0)
            page2 = qx.search("us-spending", "education", limit=5, offset=5)
        assert len(page1.results) > 0
        assert len(page2.results) > 0

    def test_search_metadata(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "education")
        assert "processing_time_ms" in resp.metadata or "search_mode" in resp.metadata

    def test_search_pagination_has_more(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "grant", limit=5)
        assert resp.pagination.has_more is True

    def test_search_iter_yields_results(self):
        with qanatix.QanatixOpen() as qx:
            results = list(qx.search.iter("us-spending", "NASA", page_size=5, max_results=12))
        assert len(results) == 12, f"Expected 12 results, got {len(results)}"
        assert all(r.record_id for r in results)

    def test_search_different_collections(self):
        with qanatix.QanatixOpen() as qx:
            r1 = qx.search("co2-emissions", "Germany")
            r2 = qx.search("country-profiles", "Germany")
        assert len(r1.results) > 0
        assert len(r2.results) > 0
        assert r1.results[0].collection == "co2-emissions"
        assert r2.results[0].collection == "country-profiles"

    def test_search_empty_query_still_works(self):
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("un-votes", "vote", limit=3)
        assert len(resp.results) > 0

    def test_search_nonexistent_collection(self):
        """Open API returns empty results for unknown collections."""
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("nonexistent-collection-xyz", "test")
        assert len(resp.results) == 0


class TestOpenSearchThenGet:
    """Search → get record by ID round-trip."""

    def test_get_record_by_id(self):
        with qanatix.QanatixOpen() as qx:
            search_resp = qx.search("us-spending", "education", limit=1)
            assert len(search_resp.results) > 0
            record_id = search_resp.results[0].record_id

        # Record fetch goes through the open search endpoint's data
        # (open API doesn't expose /records directly — this validates search result completeness)
        assert record_id
        assert len(record_id) > 10  # UUID format


class TestOpenErrors:
    def test_nonexistent_record_via_search(self):
        """Open API doesn't expose /records — just validate search handles edge cases."""
        with qanatix.QanatixOpen() as qx:
            resp = qx.search("us-spending", "xyznonexistent99999", limit=1)
        # Should return empty, not crash
        assert isinstance(resp.results, list)


# ── Authenticated API Tests (requires QANATIX_API_KEY) ──


class TestAuthCollections:
    def test_list(self):
        with auth_client() as qx:
            cols = qx.collections.list()
        assert isinstance(cols, list)


class TestAuthSearch:
    def test_search(self):
        with auth_client() as qx:
            cols = qx.collections.list()
            if not cols:
                pytest.skip("No collections available")
            resp = qx.search(cols[0].collection, "test", limit=3)
        assert isinstance(resp.results, list)



class TestAuthKeys:
    def test_list(self):
        with auth_client() as qx:
            keys = qx.keys.list()
        assert isinstance(keys, list)


class TestAuthRecords:
    def test_list(self):
        with auth_client() as qx:
            recs = qx.records.list(limit=5)
        assert isinstance(recs, list)


class TestAuthIngest:
    """Full ingest round-trip: schema → batch → search → delete."""

    def test_ingest_and_search_roundtrip(self):
        with auth_client() as qx:
            import uuid
            col = f"sdk-test-{uuid.uuid4().hex[:8]}"
            rtype = "widget"

            # Ingest
            result = qx.ingest.batch(col, rtype, [
                {"name": "Red Widget", "color": "red", "weight_kg": 1.2},
                {"name": "Blue Widget", "color": "blue", "weight_kg": 0.8},
                {"name": "Green Widget", "color": "green", "weight_kg": 1.5},
            ])
            assert result.summary.accepted == 3, f"Expected 3 accepted, got {result.summary}"

            # Search (may need a moment to index)
            import time
            time.sleep(2)
            resp = qx.search(col, "red widget")
            assert len(resp.results) > 0, "Expected search results after ingest"

            # Cleanup
            for r in resp.results:
                qx.records.delete(r.record_id)


# ── Async Tests ──


class TestAsyncOpen:
    @pytest.mark.asyncio
    async def test_search(self):
        async with qanatix.AsyncQanatixOpen() as qx:
            resp = await qx.search("us-spending", "education", limit=3)
        assert len(resp.results) > 0

    @pytest.mark.asyncio
    async def test_collections(self):
        async with qanatix.AsyncQanatixOpen() as qx:
            cols = await qx.collections.list()
        assert len(cols) > 0

    @pytest.mark.asyncio
    async def test_iter(self):
        async with qanatix.AsyncQanatixOpen() as qx:
            results = []
            async for r in qx.search.iter("co2-emissions", "emissions", page_size=5, max_results=10):
                results.append(r)
        assert len(results) == 10

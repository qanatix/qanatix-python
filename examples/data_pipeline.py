#!/usr/bin/env python3
"""Real-world example: Data Pipeline with Qanatix.

Demonstrates a production-ready data pipeline:
1. Upload data from CSV file or DataFrame
2. Search with filters and sorting
3. Bulk operations (update, delete)
4. Webhook setup for real-time notifications
5. Export data
6. Error handling best practices
7. Async operations

Usage:
    pip install qanatix[pandas]
    export QANATIX_API_KEY=sk_live_...
    python examples/data_pipeline.py
"""

import asyncio
import os
import sys

import qanatix
from qanatix import (
    AuthenticationError,
    NotFoundError,
    QanatixError,
    RateLimitError,
    ValidationError,
)

API_KEY = os.environ.get("QANATIX_API_KEY")
if not API_KEY:
    print("Set QANATIX_API_KEY environment variable")
    sys.exit(1)

COLLECTION = "pipeline_demo"


def sync_example():
    """Synchronous SDK usage — simplest approach."""
    qx = qanatix.Qanatix(API_KEY)

    print("=" * 60)
    print("Qanatix Data Pipeline Example")
    print("=" * 60)

    # ── 1. Batch ingest ──
    print("\n1. Batch ingest...")
    products = [
        {"name": "Industrial Valve DN50", "sku": "IV-DN50", "category": "valves", "price_eur": 89.50, "stock": 1200, "material": "Stainless Steel"},
        {"name": "Pressure Sensor PT100", "sku": "PS-PT100", "category": "sensors", "price_eur": 245.00, "stock": 340, "material": "Titanium"},
        {"name": "Flow Meter FM-200", "sku": "FM-200", "category": "meters", "price_eur": 1250.00, "stock": 85, "material": "Brass"},
        {"name": "Temperature Probe TP-K", "sku": "TP-K", "category": "sensors", "price_eur": 67.00, "stock": 2500, "material": "Stainless Steel"},
        {"name": "Ball Valve BV25", "sku": "BV-25", "category": "valves", "price_eur": 42.00, "stock": 5000, "material": "Carbon Steel"},
        {"name": "Level Transmitter LT-40", "sku": "LT-40", "category": "sensors", "price_eur": 890.00, "stock": 120, "material": "Ceramic"},
        {"name": "Gate Valve GV100", "sku": "GV-100", "category": "valves", "price_eur": 320.00, "stock": 450, "material": "Cast Iron"},
        {"name": "pH Meter PM-7", "sku": "PM-7", "category": "meters", "price_eur": 580.00, "stock": 200, "material": "Glass/Plastic"},
    ]

    result = qx.ingest.batch(COLLECTION, "product", products)
    print(f"   Accepted: {result.summary.accepted}, Rejected: {result.summary.rejected}")

    if result.errors:
        for err in result.errors[:3]:
            print(f"   Error: {err.message}")

    # ── 2. Search with filters ──
    print("\n2. Search with filters...")

    # Basic search
    results = qx.search(COLLECTION, "stainless steel valve", limit=5)
    print(f"   'stainless steel valve': {len(results.results)} results")
    for r in results.results:
        print(f"     {r.name} — score {r.score:.2f}")

    # Search with filters
    results = qx.search(
        COLLECTION,
        "sensor",
        filters={"category": "sensors", "price_eur_max": 300},
        sort="-price_eur",
        limit=10,
    )
    print(f"\n   Sensors under €300: {len(results.results)} results")
    for r in results.results:
        price = r.collection_data.get("price_eur", "?")
        print(f"     {r.name} — €{price}")

    # ── 3. Record CRUD ──
    print("\n3. Record operations...")

    # Create
    rec = qx.records.create(
        COLLECTION, "product", "Emergency Shutoff Valve ESV-80",
        data={"sku": "ESV-80", "category": "valves", "price_eur": 2100.00, "stock": 25, "material": "Duplex Steel"},
    )
    print(f"   Created: {rec.name} (id: {rec.record_id[:8]}...)")

    # Update
    qx.records.update(rec.record_id, data={"stock": 30, "price_eur": 1950.00})
    print(f"   Updated: stock → 30, price → €1950")

    # Get
    updated = qx.records.get(rec.record_id)
    print(f"   Verified: stock={updated.data.get('stock')}, price=€{updated.data.get('price_eur')}")

    # ── 4. Bulk operations ──
    print("\n4. Bulk operations...")
    all_ids = [r.record_id for r in qx.search.iter(COLLECTION, "", page_size=50)]
    print(f"   Total records: {len(all_ids)}")

    # ── 5. Error handling ──
    print("\n5. Error handling demo...")

    try:
        qx.records.get("00000000-0000-0000-0000-000000000000")
    except NotFoundError:
        print("   NotFoundError: correctly caught missing record")

    try:
        qx.search("nonexistent_collection", "test")
    except QanatixError as e:
        print(f"   QanatixError: {e}")

    # ── 6. Collections ──
    print("\n6. Collections...")
    for c in qx.collections.list():
        print(f"   {c.collection}: {c.record_count} records, types: {c.record_types}")

    # ── 7. Clean up ──
    print("\n7. Cleaning up...")
    deleted = qx.records.bulk_delete(all_ids)
    print(f"   Deleted {deleted} records")

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


async def async_example():
    """Async SDK usage — for high-throughput applications."""
    print("\n\n" + "=" * 60)
    print("Async Example")
    print("=" * 60)

    async with qanatix.AsyncQanatix(API_KEY) as qx:
        # Parallel searches
        print("\n1. Parallel searches...")
        results = await asyncio.gather(
            qx.search(COLLECTION, "valve"),
            qx.search(COLLECTION, "sensor"),
            qx.search(COLLECTION, "meter"),
        )
        for r in results:
            if r.results:
                print(f"   Found {len(r.results)} results for first match: {r.results[0].name}")

        # Async iteration
        print("\n2. Async iteration...")
        count = 0
        async for record in qx.search.iter(COLLECTION, "", page_size=10):
            count += 1
        print(f"   Iterated {count} records")


def open_search_example():
    """Search public data without authentication."""
    print("\n\n" + "=" * 60)
    print("Open Search (No Auth)")
    print("=" * 60)

    qx_open = qanatix.QanatixOpen()

    # List public collections
    print("\n1. Public collections...")
    try:
        collections = qx_open.collections.list()
        for c in collections[:5]:
            print(f"   {c.collection}: {c.record_count} records")
    except QanatixError as e:
        print(f"   {e}")

    # Search public data
    print("\n2. Public search...")
    try:
        results = qx_open.search("countries", "European Union")
        for r in results.results[:3]:
            print(f"   {r.name} (score: {r.score:.2f})")
    except QanatixError as e:
        print(f"   {e}")


if __name__ == "__main__":
    sync_example()
    open_search_example()
    # Uncomment to run async example (requires data in COLLECTION):
    # asyncio.run(async_example())

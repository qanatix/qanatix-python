#!/usr/bin/env python3
"""Example: ETF Dashboard — showcases Qanatix SDK end-to-end.

This script demonstrates:
1. Batch data ingestion
2. Collection listing
3. Full-text search
4. Auto-paginating search iterator
5. Record CRUD
6. Webhook subscription for real-time notifications
7. Clean up

Usage:
    pip install qanatix
    export QANATIX_API_KEY=sk_live_...
    python examples/etf_dashboard.py
"""

import os
import sys

import qanatix

API_KEY = os.environ.get("QANATIX_API_KEY")
if not API_KEY:
    print("Set QANATIX_API_KEY environment variable")
    sys.exit(1)

# You can also pass base_url for self-hosted instances
qx = qanatix.Qanatix(API_KEY)

COLLECTION = "etf_demo"
RECORD_TYPE = "etf"

# Sample ETF data
ETFS = [
    {"name": "iShares Core S&P 500 UCITS ETF", "ticker": "CSPX", "provider": "iShares", "isin": "IE00B5BMR087", "ter_percent": 0.07, "aum_eur": 82100000000, "asset_class": "equity", "replication": "physical", "distribution": "accumulating", "inception_year": 2010},
    {"name": "Vanguard FTSE All-World UCITS ETF", "ticker": "VWCE", "provider": "Vanguard", "isin": "IE00BK5BQT80", "ter_percent": 0.22, "aum_eur": 30500000000, "asset_class": "equity", "replication": "physical", "distribution": "accumulating", "inception_year": 2019},
    {"name": "Invesco Physical Gold ETC", "ticker": "SGLD", "provider": "Invesco", "isin": "IE00B579F325", "ter_percent": 0.12, "aum_eur": 15700000000, "asset_class": "commodity", "replication": "physical", "distribution": "none", "inception_year": 2009},
    {"name": "iShares Core Euro Corporate Bond UCITS ETF", "ticker": "EUCO", "provider": "iShares", "isin": "IE00B3F81R35", "ter_percent": 0.20, "aum_eur": 12300000000, "asset_class": "fixed_income", "replication": "physical", "distribution": "distributing", "inception_year": 2009},
    {"name": "Xtrackers DAX UCITS ETF", "ticker": "DBXD", "provider": "Xtrackers", "isin": "LU0274211480", "ter_percent": 0.09, "aum_eur": 4200000000, "asset_class": "equity", "replication": "physical", "distribution": "accumulating", "inception_year": 2007},
]


def main():
    print("=" * 60)
    print("Qanatix ETF Dashboard Example")
    print("=" * 60)

    # ── 1. Ingest data ──
    print("\n1. Ingesting ETF data...")
    result = qx.ingest.batch(COLLECTION, RECORD_TYPE, ETFS)
    print(f"   Submitted: {result.summary.submitted}")
    print(f"   Accepted:  {result.summary.accepted}")
    print(f"   Rejected:  {result.summary.rejected}")

    # ── 2. List collections ──
    print("\n2. Listing collections...")
    for c in qx.collections.list():
        print(f"   {c.collection}: {c.record_count} records")

    # ── 3. Search ──
    print("\n3. Searching for 'gold'...")
    results = qx.search(COLLECTION, "gold", limit=5)
    for r in results.results:
        print(f"   {r.name} (score: {r.score:.2f})")

    # ── 4. Auto-paginating iterator ──
    print("\n4. Iterating all records...")
    count = 0
    for record in qx.search.iter(COLLECTION, "", page_size=10):
        count += 1
        print(f"   [{count}] {record.name}")
    print(f"   Total: {count} records")

    # ── 5. Get a record by ID ──
    if results.results:
        print("\n5. Getting record by ID...")
        rec = qx.records.get(results.results[0].record_id)
        print(f"   Name: {rec.name}")
        print(f"   Data: {rec.data}")
        fields = list(rec.data.keys()) if rec.data else []
        print(f"   Fields: {', '.join(fields)}")

    # ── 6. Create a webhook ──
    print("\n6. Creating webhook...")
    try:
        wh = qx.webhooks.create(
            url="https://httpbin.org/post",
            events=["record.created", "upload.complete"],
            description="ETF dashboard demo",
        )
        print(f"   Webhook ID: {wh.id}")
        print(f"   Secret: {wh.secret}")

        # Test the webhook
        print("\n   Testing webhook...")
        # qx.webhooks.test(wh.id)  # uncomment to test

        # Clean up
        qx.webhooks.delete(wh.id)
        print("   Webhook deleted ✓")
    except Exception as e:
        print(f"   Webhook: {e} (may not be available)")

    # ── 7. Clean up ──
    print("\n7. Cleaning up...")
    for record in qx.search.iter(COLLECTION, "", page_size=50):
        qx.records.delete(record.record_id)
    print("   Records deleted ✓")

    print("\n" + "=" * 60)
    print("Done! All Qanatix SDK features demonstrated.")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Quickstart: Qanatix SDK in 5 minutes.

Demonstrates the core SDK workflow:
1. Ingest data (batch JSON)
2. Search with natural language
3. List and browse records
4. Auto-paginate through results
5. Clean up

Usage:
    pip install qanatix
    export QANATIX_API_KEY=sk_live_...
    python examples/quickstart.py
"""

import os
import sys

import qanatix

API_KEY = os.environ.get("QANATIX_API_KEY")
if not API_KEY:
    print("Set QANATIX_API_KEY environment variable")
    sys.exit(1)

qx = qanatix.Qanatix(API_KEY)

COLLECTION = "demo_companies"
RECORD_TYPE = "company"

# Sample data
COMPANIES = [
    {"name": "Acme Corp", "industry": "Manufacturing", "country": "US", "revenue_usd": 4200000, "employees": 850, "founded": 2001},
    {"name": "Globex Inc", "industry": "Technology", "country": "US", "revenue_usd": 12800000, "employees": 320, "founded": 2015},
    {"name": "Initech GmbH", "industry": "Software", "country": "DE", "revenue_usd": 3100000, "employees": 95, "founded": 2018},
    {"name": "Umbrella Ltd", "industry": "Pharmaceuticals", "country": "GB", "revenue_usd": 89000000, "employees": 4200, "founded": 1985},
    {"name": "Stark Industries", "industry": "Defense", "country": "US", "revenue_usd": 210000000, "employees": 15000, "founded": 1970},
    {"name": "Wayne Enterprises", "industry": "Conglomerate", "country": "US", "revenue_usd": 95000000, "employees": 8500, "founded": 1939},
    {"name": "Oscorp", "industry": "Biotechnology", "country": "US", "revenue_usd": 45000000, "employees": 2100, "founded": 1998},
    {"name": "Cyberdyne Systems", "industry": "Robotics", "country": "JP", "revenue_usd": 67000000, "employees": 1800, "founded": 2003},
    {"name": "Soylent Corp", "industry": "Food & Beverage", "country": "US", "revenue_usd": 15000000, "employees": 600, "founded": 2010},
    {"name": "Weyland-Yutani", "industry": "Aerospace", "country": "GB", "revenue_usd": 180000000, "employees": 12000, "founded": 1960},
]


def main():
    print("=" * 50)
    print("Qanatix SDK Quickstart")
    print("=" * 50)

    # 1. Ingest data
    print("\n1. Ingesting company data...")
    result = qx.ingest.batch(COLLECTION, RECORD_TYPE, COMPANIES)
    print(f"   Accepted: {result.summary.accepted}")
    print(f"   Rejected: {result.summary.rejected}")

    # 2. Search
    print("\n2. Searching for 'technology US'...")
    results = qx.search(COLLECTION, "technology US", limit=5)
    for r in results.results:
        print(f"   {r.name} (score: {r.score:.2f})")

    # 3. List collections
    print("\n3. Listing collections...")
    for c in qx.collections.list():
        print(f"   {c.collection}: {c.record_count} records")

    # 4. Get a record by ID
    if results.results:
        print("\n4. Getting record details...")
        rec = qx.records.get(results.results[0].record_id)
        print(f"   Name: {rec.name}")
        print(f"   Data: {rec.data}")

    # 5. Auto-paginate
    print("\n5. Iterating all records...")
    count = 0
    for record in qx.search.iter(COLLECTION, "", page_size=5):
        count += 1
        print(f"   [{count}] {record.name}")
    print(f"   Total: {count}")

    # 6. Clean up
    print("\n6. Cleaning up...")
    for record in qx.search.iter(COLLECTION, "", page_size=50):
        qx.records.delete(record.record_id)
    print("   Done.")

    print("\n" + "=" * 50)
    print("Quickstart complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()

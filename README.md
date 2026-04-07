# Qanatix Python SDK

The official Python SDK for [Qanatix](https://qanatix.com) — ingest, search, and manage structured data for AI agents.

## Install

```bash
pip install qanatix
```

With pandas support:

```bash
pip install qanatix[pandas]
```

## Quick start

```python
import qanatix

qx = qanatix.Qanatix("sk_live_...")

# Search
results = qx.search("parts_catalog", "stainless M8 bolt")
for r in results.results:
    print(r.name, r.score)

# Ingest
result = qx.ingest.batch("parts_catalog", "fastener", [
    {"name": "Hex Bolt M8x40", "material": "stainless", "price_eur": 0.12},
    {"name": "Hex Nut M8", "material": "carbon steel", "price_eur": 0.04},
])
print(f"Accepted: {result.summary.accepted}")

# Records
rec = qx.records.create("parts_catalog", "fastener", "New Part", {"price_eur": 1.50})
print(rec.record_id)
```

## Public data (no API key)

```python
import qanatix

# Open — with agent identification (recommended)
qx = qanatix.QanatixOpen(agent_id="my-app-name")

# Open — anonymous (still works)
qx = qanatix.QanatixOpen()

results = qx.search("suppliers", "ISO 9001 certified Germany")
collections = qx.collections.list()
```

## Async

```python
import qanatix

# Private
async with qanatix.AsyncQanatix("sk_live_...") as qx:
    results = await qx.search("parts_catalog", "stainless bolt")

# Open
async with qanatix.AsyncQanatixOpen() as qx:
    results = await qx.search("suppliers", "CNC machining Germany")
```

## Clients

| Client | Auth | Resources |
|---|---|---|
| `Qanatix("sk_live_...")` | API key | All resources |
| `QanatixOpen()` | None | search, collections |
| `AsyncQanatix("sk_live_...")` | API key | All resources, async |
| `AsyncQanatixOpen()` | None | search, collections, async |

## Features

- **Search** — full-text + filters, auto-paginating iterator via `qx.search.iter()`
- **Ingest** — batch JSON, file upload (CSV/JSON/XML), DataFrame support
- **Auto-chunking** — batches >5,000 records split automatically
- **Retry** — exponential backoff on 429/502/503/504
- **Records** — CRUD + bulk update/delete
- **Connectors** — pull from PostgreSQL, MySQL, MongoDB, Neo4j
- **Collections** — list and update collection metadata
- **API Keys** — create, list, revoke, rotate
- **Webhooks** — create, list, test, and delete webhook subscriptions + `verify_signature()` for incoming payloads
- **Sync + Async** — `Qanatix` / `AsyncQanatix` + `QanatixOpen` / `AsyncQanatixOpen`

## All methods

| Method | Description |
|---|---|
| `qx.search(col, query, ...)` | Search a collection |
| `qx.search.iter(col, query, ...)` | Auto-paginate search results |
| `qx.records.create(...)` | Create a record |
| `qx.records.get(id)` | Get a record by ID |
| `qx.records.list(...)` | List records |
| `qx.records.update(id, ...)` | Update a record |
| `qx.records.delete(id)` | Delete a record |
| `qx.records.bulk_update(ids, ...)` | Bulk update records |
| `qx.records.bulk_delete(ids)` | Bulk delete records |
| `qx.ingest.batch(col, type, records)` | Ingest JSON batch |
| `qx.ingest.upload(col, type, path)` | Upload file |
| `qx.ingest.from_dataframe(col, type, df)` | Ingest from DataFrame |
| `qx.ingest.status(upload_id)` | Check upload status |
| `qx.ingest.errors(upload_id)` | Get upload errors |
| `qx.connectors.create(...)` | Create a connector |
| `qx.connectors.list()` | List connectors |
| `qx.connectors.pull(id)` | Trigger a pull |
| `qx.connectors.delete(id)` | Delete a connector |
| `qx.collections.list()` | List collections |
| `qx.collections.update(name, ...)` | Update collection metadata |
| `qx.keys.create(name, scopes)` | Create an API key |
| `qx.keys.list()` | List API keys |
| `qx.keys.revoke(id)` | Revoke an API key |
| `qx.keys.rotate(id)` | Rotate an API key |
| `qx.webhooks.create(url, events, ...)` | Create a webhook subscription |
| `qx.webhooks.list()` | List webhooks |
| `qx.webhooks.delete(id)` | Delete a webhook |
| `qx.webhooks.test(id)` | Send a test event |
| `qx.webhooks.deliveries(id)` | View delivery history |
| `qx.chat(message, history)` | Ask questions about your data in natural language |
| `qx.export(col, format)` | Stream export |

## Chat

Ask questions about your data in natural language — Qanatix handles the rest:

```python
answer = qx.chat("Show me ETFs with fees under 0.1%")
print(answer)

# With conversation history
answer = qx.chat("Compare them by AUM", history=[
    {"role": "user", "content": "Show me ETFs with fees under 0.1%"},
    {"role": "assistant", "content": "...previous answer..."},
])
```

Each chat message counts as 1 search against your quota.

## Docs

Full documentation at [qanatix.dev/docs/getting-started/python-sdk](https://qanatix.dev/docs/getting-started/python-sdk)

## License

MIT

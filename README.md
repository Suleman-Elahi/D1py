# D1py

A modern, async Python client for the [Cloudflare D1](https://developers.cloudflare.com/d1/) REST API.

D1 is Cloudflare's serverless SQLite-based database. D1py gives you full programmatic access to manage databases, run queries, import/export data, and use time-travel — all from Python with first-class async support.

## Highlights

- **Async-first** — built on `httpx.AsyncClient` with HTTP/2 and connection pooling for high throughput
- **Full D1 API** — every endpoint covered: database CRUD, queries, batches, export/import, time travel
- **Type-safe** — Pydantic v2 models for all request params and responses, full IDE autocomplete
- **Sync fallback** — every method has a `*_sync()` variant for scripts and notebooks
- **Automatic retries** — exponential backoff on 5xx and network errors, configurable
- **Context manager** — clean resource lifecycle with `async with`

## Install

```bash
pip install d1py
```

From source:

```bash
git clone https://github.com/Suleman-Elahi/D1py && cd D1py
pip install .
```

Requires Python 3.10+. Dependencies: `httpx`, `pydantic`.

## Quick Example

```python
import asyncio
from D1py import D1py

async def main():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        db = await d1.create_database("my-app")
        await d1.query(db.uuid, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        await d1.query(db.uuid, "INSERT INTO users (name) VALUES (?)", params=["Alice"])
        results = await d1.query(db.uuid, "SELECT * FROM users")
        print(results[0].results)

asyncio.run(main())
```

## Documentation

| Guide | What it covers |
|-------|---------------|
| [Getting Started](docs/getting-started.md) | Installation, authentication, first query |
| [Database Management](docs/database-management.md) | Create, list, get, update, delete databases |
| [Queries](docs/queries.md) | Single queries, parameterized queries, batch queries, raw queries |
| [Export & Import](docs/export-import.md) | Export databases to SQL, import SQL files |
| [Time Travel](docs/time-travel.md) | Bookmarks, restore to point-in-time |
| [Configuration](docs/configuration.md) | Client options, timeouts, retries, connection pooling |
| [Error Handling](docs/error-handling.md) | Exception types, error codes, retry behavior |
| [Async vs Sync](docs/async-vs-sync.md) | When to use async, sync wrappers, patterns |

## API At a Glance

**Database management:** `list_databases`, `create_database`, `get_database`, `update_database`, `patch_database`, `delete_database`

**Queries:** `query`, `query_batch`, `raw_query`, `raw_query_batch`

**Data ops:** `export_database`, `import_database`

**Time travel:** `get_bookmark`, `restore`

Every async method has a sync counterpart (e.g. `query_sync`, `create_database_sync`).

## License

MIT

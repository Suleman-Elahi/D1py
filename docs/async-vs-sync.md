# Async vs Sync

D1py is built async-first but provides sync wrappers for every method. Choose the right approach for your use case.

## Async (Recommended)

Use async methods in:

- Web applications (FastAPI, Flask with async, Starlette)
- Scripts that make many concurrent requests
- Any existing async codebase

```python
import asyncio
from D1py import D1py

async def main():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        results = await d1.query(database_id, "SELECT * FROM users")
        for row in results[0].results:
            print(row)

asyncio.run(main())
```

### Why Async?

- **Non-blocking** — other code runs while waiting for API responses
- **Concurrent requests** — fire multiple queries in parallel
- **Connection pooling** — `httpx.AsyncClient` reuses connections automatically

### Concurrent Queries

```python
import asyncio
from D1py import D1py

async def main():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        # Run 3 queries in parallel
        results = await asyncio.gather(
            d1.query(db_id, "SELECT COUNT(*) FROM users"),
            d1.query(db_id, "SELECT COUNT(*) FROM posts"),
            d1.query(db_id, "SELECT COUNT(*) FROM comments"),
        )
        print(f"Users: {results[0][0].results[0]}")
        print(f"Posts: {results[1][0].results[0]}")
        print(f"Comments: {results[2][0].results[0]}")

asyncio.run(main())
```

## Sync

Use sync methods in:

- Simple scripts and CLI tools
- Jupyter notebooks
- Code that can't use `async/await`
- Quick one-off operations

```python
from D1py import D1py

d1 = D1py(account_id="xxx", api_token="xxx")
results = d1.query_sync(database_id, "SELECT * FROM users")
for row in results[0].results:
    print(row)
```

### Sync Method Naming

Every async method has a `_sync` suffix:

| Async | Sync |
|-------|------|
| `await d1.query(...)` | `d1.query_sync(...)` |
| `await d1.create_database(...)` | `d1.create_database_sync(...)` |
| `await d1.list_databases(...)` | `d1.list_databases_sync()` |
| `await d1.export_database(...)` | `d1.export_database_sync(...)` |
| `await d1.restore(...)` | `d1.restore_sync(...)` |

### Context Manager

Sync methods don't need the `async with` block — just create and use the client:

```python
d1 = D1py(account_id="xxx", api_token="xxx")
d1.query_sync(db_id, "SELECT 1")
```

## Comparison

| | Async | Sync |
|--|-------|------|
| Syntax | `await d1.method()` | `d1.method_sync()` |
| Context manager | `async with D1py(...) as d1:` | Not required |
| Performance | Non-blocking, concurrent | Blocking, sequential |
| Best for | Web apps, scripts, notebooks | Simple scripts, CLI tools |
| Event loop | Required (`asyncio.run`) | None |

## Common Patterns

### Script with Error Handling

```python
# sync/script.py
import os
from D1py import D1py
from D1py.exceptions import D1APIError

d1 = D1py(
    account_id=os.environ["CF_ACCOUNT_ID"],
    api_token=os.environ["CF_API_TOKEN"],
)

try:
    results = d1.query_sync(
        os.environ["DB_ID"],
        "SELECT * FROM users WHERE active = ?",
        params=["1"],
    )
    for row in results[0].results:
        print(row["name"])
except D1APIError as e:
    print(f"Query failed: {e}")
```

### Web Framework (FastAPI)

```python
# async/web.py
from fastapi import FastAPI
from D1py import D1py

app = FastAPI()
d1 = D1py(account_id="xxx", api_token="xxx")

@app.get("/users")
async def get_users():
    results = await d1.query("db-id", "SELECT * FROM users")
    return results[0].results

@app.on_event("shutdown")
async def shutdown():
    await d1.close()
```

### Notebook

```python
# In a Jupyter cell
from D1py import D1py

d1 = D1py(account_id="xxx", api_token="xxx")

# Use sync methods in notebooks
databases, _ = d1.list_databases_sync()
for db in databases:
    print(db.name)

# Or use async if the notebook supports it
# results = await d1.query(db_id, "SELECT * FROM users")
```

## Next Steps

- [Configuration](configuration.md) — timeouts, retries, connection pooling
- [Error Handling](error-handling.md) — exception types and patterns

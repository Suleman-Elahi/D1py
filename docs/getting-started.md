# Getting Started

This guide walks you through installing D1py, authenticating with Cloudflare, and running your first query.

## Prerequisites

- Python 3.10 or later
- A Cloudflare account with D1 enabled
- A Cloudflare API token with D1 permissions

### Creating an API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → My Profile → API Tokens
2. Click **Create Token**
3. Use the **Edit Cloudflare Workers** template, or create a custom token with `Account > D1 > Edit` permission
4. Copy the token — you'll need it below

## Installation

```bash
pip install d1py
```

Or install from source:

```bash
git clone https://github.com/Suleman-Elahi/D1py && cd D1py
pip install .
```

## Authentication

D1py needs your Cloudflare **Account ID** and **API Token**.

```python
from D1py import D1py

d1 = D1py(
    account_id="your-account-id",
    api_token="your-api-token",
)
```

> **Tip:** Store credentials in environment variables, not in code.
>
> ```python
> import os
> d1 = D1py(
>     account_id=os.environ["CF_ACCOUNT_ID"],
>     api_token=os.environ["CF_API_TOKEN"],
> )
> ```

## Your First Query

### Async (recommended)

```python
import asyncio
from D1py import D1py

async def main():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        # List existing databases
        databases, info = await d1.list_databases()
        print(f"You have {info.total_count} database(s)")

        # Create a new one
        db = await d1.create_database("hello-world")
        print(f"Created: {db.name} ({db.uuid})")

        # Create a table and insert data
        await d1.query(db.uuid, """
            CREATE TABLE greeting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL
            )
        """)
        await d1.query(
            db.uuid,
            "INSERT INTO greeting (message) VALUES (?)",
            params=["Hello from D1py!"],
        )

        # Read it back
        results = await d1.query(db.uuid, "SELECT * FROM greeting")
        for row in results[0].results:
            print(row)

asyncio.run(main())
```

### Sync

```python
from D1py import D1py

d1 = D1py(account_id="xxx", api_token="xxx")

databases, info = d1.list_databases_sync()
print(f"You have {info.total_count} database(s)")
```

See [Async vs Sync](async-vs-sync.md) for when to use each approach.

## What's Next

- [Database Management](database-management.md) — create, list, update, delete databases
- [Queries](queries.md) — parameterized queries, batches, raw queries
- [Configuration](configuration.md) — timeouts, retries, connection pooling

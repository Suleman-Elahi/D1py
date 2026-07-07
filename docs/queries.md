# Queries

Run SQL queries against D1 databases — single statements, parameterized queries, batches, and raw optimized queries.

See also: [Database Management](database-management.md) to create a database first.

## Single Query

```python
results = await d1.query(database_id, "SELECT * FROM users")

for row in results[0].results:
    print(row)  # dict like {"id": 1, "name": "Alice"}
```

`query()` returns a list of `QueryResult` objects — one per SQL statement. Each contains:

| Field | Type | Description |
|-------|------|-------------|
| `results` | `list[dict]` | Row data as dictionaries |
| `meta` | `QueryMeta` | Execution metadata (duration, rows read/written, etc.) |
| `success` | `bool` | Whether the statement succeeded |

## Parameterized Queries

Always use parameters for user input — D1 handles escaping:

```python
results = await d1.query(
    database_id,
    "SELECT * FROM users WHERE age > ? AND country = ?",
    params=["25", "US"],
)
```

```python
# Insert with parameters
await d1.query(
    database_id,
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    params=["Bob", "bob@example.com", "30"],
)
```

```python
# Update
await d1.query(
    database_id,
    "UPDATE users SET email = ? WHERE id = ?",
    params=["new@example.com", "42"],
)
```

```python
# Delete
await d1.query(database_id, "DELETE FROM users WHERE id = ?", params=["42"])
```

## Query Metadata

Every query result includes performance metadata:

```python
results = await d1.query(database_id, "SELECT * FROM users")
meta = results[0].meta

print(f"Duration: {meta.duration}ms")
print(f"Rows read: {meta.rows_read}")
print(f"Rows written: {meta.rows_written}")
print(f"Region: {meta.served_by_region}")
print(f"Colo: {meta.served_by_colo}")
```

## Batch Queries

Execute multiple statements in a single API call — faster than individual queries:

```python
results = await d1.query_batch(database_id, [
    {"sql": "INSERT INTO users (name) VALUES (?)", "params": ["Alice"]},
    {"sql": "INSERT INTO users (name) VALUES (?)", "params": ["Bob"]},
    {"sql": "SELECT COUNT(*) as total FROM users"},
])

# results[2].results[0]["total"] == 2
```

Each item in the batch is a dict with `"sql"` and optional `"params"`.

## Raw Queries

The `/raw` endpoint returns results as column arrays + row arrays instead of dictionaries. This is more efficient for large result sets:

```python
results = await d1.raw_query(database_id, "SELECT * FROM users")

raw = results[0].results
print(raw.columns)  # ["id", "name", "email"]
print(raw.rows)     # [[1, "Alice", "alice@ex.com"], [2, "Bob", "bob@ex.com"]]
```

### When to Use Raw vs Standard

| | `query()` | `raw_query()` |
|--|-----------|---------------|
| Result format | `list[dict]` | columns + rows arrays |
| Memory | Higher (dict per row) | Lower (array per row) |
| Use case | General purpose, small-medium results | Large exports, data processing |

## Raw Batch Queries

```python
results = await d1.raw_query_batch(database_id, [
    {"sql": "SELECT * FROM users"},
    {"sql": "SELECT * FROM posts"},
])

for r in results:
    print(r.results.columns, len(r.results.rows), "rows")
```

## Multi-Statement SQL

D1 supports multiple semicolon-separated statements in a single query:

```python
results = await d1.query(database_id, """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT
    );
    INSERT INTO items (name) VALUES ('Widget');
    SELECT * FROM items;
""")
# results[0] = CREATE result
# results[1] = INSERT result
# results[2] = SELECT result with the inserted row
```

## Practical Example: CRUD Operations

```python
async def user_crud():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        db = await d1.create_database("users-app")

        # Setup
        await d1.query(db.uuid, """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create
        await d1.query(
            db.uuid,
            "INSERT INTO users (name, email) VALUES (?, ?)",
            params=["Alice", "alice@example.com"],
        )

        # Read
        result = await d1.query(db.uuid, "SELECT * FROM users WHERE name = ?", params=["Alice"])
        print(result[0].results)

        # Update
        await d1.query(
            db.uuid,
            "UPDATE users SET email = ? WHERE name = ?",
            params=["alice@newdomain.com", "Alice"],
        )

        # Delete
        await d1.query(db.uuid, "DELETE FROM users WHERE name = ?", params=["Alice"])

        # List all
        result = await d1.query(db.uuid, "SELECT * FROM users")
        print(f"Remaining users: {len(result[0].results)}")
```

## Next Steps

- [Export & Import](export-import.md) — backup your data or import SQL dumps
- [Time Travel](time-travel.md) — restore to a previous state

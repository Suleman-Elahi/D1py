# Time Travel

D1 supports time-travel: get a bookmark representing the database state at a point in time, then restore to that bookmark.

See also: [Export & Import](export-import.md) for full database dumps.

## How It Works

Every D1 database maintains a history of states. A **bookmark** is a opaque string that identifies a specific point in time. You can:

1. **Get** the current bookmark (or the nearest one before a timestamp)
2. **Restore** the database to any bookmark or timestamp

## Get Current Bookmark

```python
bookmark = await d1.get_bookmark(database_id)
print(f"Current bookmark: {bookmark.bookmark}")
```

## Get Bookmark at a Timestamp

Find the nearest available state before a specific time:

```python
bookmark = await d1.get_bookmark(
    database_id,
    timestamp="2024-06-15T14:30:00Z",
)
print(f"Nearest bookmark: {bookmark.bookmark}")
```

## Restore to a Bookmark

```python
result = await d1.restore(database_id, bookmark="00000001-00000002-...")
print(f"Restored: {result.message}")
print(f"Previous bookmark: {result.previous_bookmark}")
```

## Restore to a Timestamp

```python
result = await d1.restore(
    database_id,
    timestamp="2024-06-15T14:00:00Z",
)
print(f"Restored to state at 14:00: {result.message}")
```

## Practical Example: Safe Migration

Before running a destructive migration, save a bookmark so you can roll back:

```python
async def safe_migration():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        db_id = "your-database-id"

        # 1. Save current state
        before = await d1.get_bookmark(db_id)
        print(f"Bookmark before migration: {before.bookmark}")

        # 2. Run migration
        await d1.query(db_id, """
            ALTER TABLE users ADD COLUMN phone TEXT;
            UPDATE users SET phone = 'unknown' WHERE phone IS NULL;
        """)

        # 3. If something goes wrong, restore
        # await d1.restore(db_id, bookmark=before.bookmark)
        # print("Rolled back!")
```

## Practical Example: Audit Trail

Save bookmarks at key moments for an audit trail:

```python
async def audited_updates():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        db_id = "your-database-id"

        checkpoints = []

        # Pre-deploy
        bm = await d1.get_bookmark(db_id)
        checkpoints.append(("pre-deploy", bm.bookmark))

        # Deploy changes
        await d1.query(db_id, "UPDATE config SET version = '2.0'")

        # Post-deploy
        bm = await d1.get_bookmark(db_id)
        checkpoints.append(("post-deploy", bm.bookmark))

        for label, bookmark in checkpoints:
            print(f"{label}: {bookmark}")
```

## Practical Example: Undo Last Operation

```python
async def undo_last_insert():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        db_id = "your-database-id"

        # Get state before the insert
        bookmark = await d1.get_bookmark(db_id)

        # Do something
        await d1.query(db_id, "INSERT INTO logs (msg) VALUES (?)", params=["oops"])

        # Undo it
        await d1.restore(db_id, bookmark=bookmark.bookmark)
        print("Undone")
```

## Response Fields

### `TimeTravelBookmark`

| Field | Type | Description |
|-------|------|-------------|
| `bookmark` | `str` | Opaque bookmark string |

### `TimeTravelRestore`

| Field | Type | Description |
|-------|------|-------------|
| `bookmark` | `str` | New bookmark after restore |
| `message` | `str` | Human-readable result |
| `previous_bookmark` | `str` | Bookmark before restore (for undo) |

## Next Steps

- [Error Handling](error-handling.md) — handle failures in time-travel operations
- [Configuration](configuration.md) — adjust timeouts for large restore operations

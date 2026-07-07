# Database Management

Create, list, inspect, update, and delete D1 databases.

See also: [Getting Started](getting-started.md) for initial setup.

## List Databases

```python
databases, info = await d1.list_databases()

for db in databases:
    print(f"{db.name} — {db.uuid} — {db.num_tables} tables — {db.file_size} bytes")
```

### Pagination

```python
# Page 1, 10 results per page
databases, info = await d1.list_databases(page=1, per_page=10)
print(f"Showing {info.count} of {info.total_count} total")
```

### Filter by Name

```python
databases, _ = await d1.list_databases(name="production")
```

## Create a Database

```python
db = await d1.create_database("my-database")
print(f"Created: {db.uuid}")
```

### With Options

```python
db = await d1.create_database(
    "eu-analytics",
    jurisdiction="eu",                      # Restrict to EU data residency
    primary_location_hint="weur",           # Primary in Western Europe
    read_replication_mode="auto",           # Enable global read replicas
)
```

**Jurisdiction values:** `"eu"`, `"fedramp"`

**Location hints:** `"wnam"`, `"enam"`, `"weur"`, `"eeur"`, `"apac"`, `"oc"`

**Replication modes:** `"auto"`, `"disabled"`

## Get a Database

```python
db = await d1.get_database(database_id)
print(f"Name: {db.name}, Tables: {db.num_tables}, Size: {db.file_size}")
```

### Select Specific Fields

```python
db = await d1.get_database(database_id, fields=["uuid", "name", "file_size"])
# Only those fields are populated; others are None
```

## Update a Database

Full update (PUT) — replaces the entire configuration:

```python
db = await d1.update_database(
    database_id,
    read_replication_mode="auto",
)
```

Partial update (PATCH) — updates only specified fields:

```python
db = await d1.patch_database(
    database_id,
    read_replication_mode="disabled",
)
```

## Delete a Database

```python
await d1.delete_database(database_id)
```

> **Warning:** This is permanent. Consider using [Time Travel](time-travel.md) to create a bookmark first.

## Full CRUD Example

```python
async def manage_databases():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        # Create
        db = await d1.create_database("temp-db")
        print(f"Created: {db.name}")

        # Read
        db = await d1.get_database(db.uuid)
        print(f"Tables: {db.num_tables}")

        # Update
        db = await d1.patch_database(db.uuid, read_replication_mode="auto")

        # List
        databases, _ = await d1.list_databases()
        for d in databases:
            print(f"  - {d.name}")

        # Delete
        await d1.delete_database(db.uuid)
        print("Deleted")
```

## Next Steps

- [Queries](queries.md) — run SQL against your database
- [Export & Import](export-import.md) — backup and restore data

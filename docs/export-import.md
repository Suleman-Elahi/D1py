# Export & Import

Export a D1 database to SQL, and import SQL content into a database.

See also: [Queries](queries.md) for running SQL directly.

## Export Database

Export creates a SQL dump file and returns a signed download URL. The method handles polling automatically — just call it and wait:

```python
result = await d1.export_database(database_id)

print(f"Status: {result.status}")
print(f"Download URL: {result.result['signed_url']}")
print(f"Filename: {result.result['filename']}")
```

The signed URL is valid for **one hour**. Download the file with any HTTP client:

```python
import httpx

result = await d1.export_database(database_id)
url = result.result["signed_url"]

async with httpx.AsyncClient() as client:
    resp = await client.get(url)
    sql_content = resp.text
    with open("backup.sql", "w") as f:
        f.write(sql_content)
```

### Export Specific Tables

```python
result = await d1.export_database(database_id, tables=["users", "posts"])
```

### Export Schema Only (No Data)

```python
result = await d1.export_database(database_id, no_data=True)
```

### Export Data Only (No Schema)

```python
result = await d1.export_database(database_id, no_schema=True)
```

## Import SQL

Import handles the full flow: init upload, upload to R2, ingest, and poll until complete:

```python
sql_content = open("backup.sql").read()
result = await d1.import_database(database_id, sql_content)

print(f"Status: {result.status}")
print(f"Queries executed: {result.result['num_queries']}")
```

### Import from String

```python
result = await d1.import_database(database_id, """
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
    INSERT INTO users (name) VALUES ('Alice');
    INSERT INTO users (name) VALUES ('Bob');
""")
```

### Error Handling

```python
try:
    result = await d1.import_database(database_id, sql_content)
    if result.status == "error":
        print(f"Import failed: {result.error}")
    else:
        print(f"Imported {result.result['num_queries']} queries")
except D1APIError as e:
    print(f"API error: {e}")
```

## Practical Example: Backup and Restore

```python
import httpx
from D1py import D1py

async def backup_and_restore():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        source_db = "abc-123-def"
        target_db = "xyz-789-uvw"

        # 1. Export from source
        export = await d1.export_database(source_db)
        if export.status != "complete":
            print(f"Export failed: {export.error}")
            return

        # 2. Download SQL
        url = export.result["signed_url"]
        async with httpx.AsyncClient() as http:
            resp = await http.get(url)
            sql = resp.text

        # 3. Import into target
        import_result = await d1.import_database(target_db, sql)
        if import_result.status == "complete":
            print(f"Restored {import_result.result['num_queries']} queries")
        else:
            print(f"Import failed: {import_result.error}")
```

## Practical Example: Clone a Database

```python
async def clone_database():
    async with D1py(account_id="xxx", api_token="xxx") as d1:
        # Export
        export = await d1.export_database("original-db-id")
        sql = httpx.get(export.result["signed_url"]).text

        # Create new DB and import
        new_db = await d1.create_database("original-db-clone")
        await d1.import_database(new_db.uuid, sql)
        print(f"Cloned to {new_db.uuid}")
```

## Next Steps

- [Time Travel](time-travel.md) — restore to a point-in-time without a full import
- [Configuration](configuration.md) — adjust timeouts for large imports/exports

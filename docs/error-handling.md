# Error Handling

D1py provides a structured exception hierarchy for handling API errors, network failures, and validation issues.

See also: [Configuration](configuration.md) for retry behavior.

## Exception Hierarchy

```
D1Error                  ← Base exception for all D1py errors
├── D1APIError           ← API returned an error response
└── D1ValidationError    ← Request validation failed before sending
```

## D1APIError

Raised when the D1 API returns a non-success response. This covers bad SQL, missing databases, auth failures, etc.

```python
from D1py import D1py
from D1py.exceptions import D1APIError

async with D1py(account_id="xxx", api_token="xxx") as d1:
    try:
        await d1.query(database_id, "SELECT * FROM nonexistent_table")
    except D1APIError as e:
        print(f"Error code: {e.code}")       # e.g. 7500
        print(f"Message: {e}")               # e.g. "no such table: nonexistent_table"
        print(f"Details: {e.errors}")        # Raw error list from API
```

### Error Codes

Common D1 error codes:

| Code | Meaning |
|------|---------|
| 7500 | SQL error (bad syntax, missing table/column) |
| 7501 | Database not found |
| 7502 | Account not authorized |
| 7503 | Database already exists |

### Checking Error Details

```python
try:
    await d1.query(db_id, "BAD SQL")
except D1APIError as e:
    if e.code == 7500:
        print(f"SQL error: {e}")
    elif e.code == 7501:
        print("Database not found — check your database_id")
    else:
        print(f"Unexpected error {e.code}: {e}")
```

## D1Error

Base class for all D1py errors. Catch this to handle any failure:

```python
from D1py.exceptions import D1Error

try:
    results = await d1.query(db_id, "SELECT 1")
except D1Error as e:
    print(f"D1py error: {e}")
```

This catches both `D1APIError` and network/timeout errors (after retries are exhausted).

## Network Errors

After all retries are exhausted, `D1Error` is raised with the last network exception:

```python
try:
    results = await d1.query(db_id, "SELECT 1")
except D1Error as e:
    if "Request failed after" in str(e):
        print("All retries failed — check your network connection")
    else:
        print(f"Error: {e}")
```

## Handling HTTP Status Codes

D1py handles 4xx errors by parsing the API response. For unexpected 4xx errors:

```python
try:
    await d1.query(db_id, "SELECT 1")
except D1APIError as e:
    if e.code is None:
        # Raw HTTP error without D1 error code
        print(f"HTTP error: {e}")
```

## Graceful Degradation Pattern

```python
async def safe_query(d1, db_id, sql, params=None):
    """Run a query with full error handling."""
    try:
        results = await d1.query(db_id, sql, params=params)
        return results
    except D1APIError as e:
        if e.code == 7500:
            print(f"SQL error — check your query: {e}")
        elif e.code == 7501:
            print("Database not found")
        else:
            print(f"API error [{e.code}]: {e}")
        return None
    except D1Error as e:
        print(f"Request failed: {e}")
        return None
```

## Retry Behavior

D1py retries automatically on transient failures:

```
Attempt 1 → 500 error → wait 0.5s
Attempt 2 → 500 error → wait 1.0s
Attempt 3 → fails → raise D1Error
```

Configure with `max_retries`:

```python
# More retries for flaky networks
d1 = D1py(account_id="xxx", api_token="xxx", max_retries=5)

# Fail fast
d1 = D1py(account_id="xxx", api_token="xxx", max_retries=1)
```

## Next Steps

- [Async vs Sync](async-vs-sync.md) — sync methods raise the same exceptions
- [Configuration](configuration.md) — adjust retry and timeout settings

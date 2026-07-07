# Configuration

Tune the D1py client for your use case: timeouts, retries, and connection pooling.

## Client Options

```python
from D1py import D1py

d1 = D1py(
    account_id="your-account-id",
    api_token="your-api-token",
    timeout=30.0,        # Per-request timeout in seconds (default: 30)
    max_retries=3,       # Retry attempts for transient failures (default: 3)
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `account_id` | required | Your Cloudflare account ID |
| `api_token` | required | Cloudflare API token with D1 permissions |
| `timeout` | `30.0` | HTTP request timeout in seconds |
| `max_retries` | `3` | Number of retry attempts on 5xx/network errors |

## Timeouts

Increase the timeout for large queries or import/export operations:

```python
# Long timeout for bulk operations
d1 = D1py(account_id="xxx", api_token="xxx", timeout=120.0)

# Quick timeout for fast-fail scenarios
d1 = D1py(account_id="xxx", api_token="xxx", timeout=5.0)
```

## Retries

D1py automatically retries on:
- **5xx errors** (server errors)
- **Network errors** (connection timeouts, DNS failures)

It does **not** retry on:
- **4xx errors** (client errors like 401, 404, 422)

Retry uses exponential backoff: 0.5s, 1s, 2s, ... up to `max_retries` attempts.

```python
# No retries — fail immediately
d1 = D1py(account_id="xxx", api_token="xxx", max_retries=1)

# Aggressive retries
d1 = D1py(account_id="xxx", api_token="xxx", max_retries=5)
```

## Connection Pooling

The underlying `httpx.AsyncClient` manages a connection pool automatically:

| Setting | Value |
|---------|-------|
| Max connections | 100 |
| Max keepalive | 20 |
| Keepalive expiry | 30 seconds |

These are optimized for typical D1 workloads. You don't need to change them unless you're hitting connection limits.

## Environment Variables

Keep secrets out of code:

```python
import os
from D1py import D1py

d1 = D1py(
    account_id=os.environ["CF_ACCOUNT_ID"],
    api_token=os.environ["CF_API_TOKEN"],
)
```

```bash
export CF_ACCOUNT_ID="your-account-id"
export CF_API_TOKEN="your-api-token"
```

## Multiple Clients

You can create separate clients for different databases or environments:

```python
prod = D1py(account_id="xxx", api_token=os.environ["PROD_TOKEN"])
staging = D1py(account_id="xxx", api_token=os.environ["STAGING_TOKEN"])
```

## Next Steps

- [Error Handling](error-handling.md) — exception types and retry behavior
- [Async vs Sync](async-vs-sync.md) — choosing the right interface

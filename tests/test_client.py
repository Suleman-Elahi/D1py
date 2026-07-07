"""Comprehensive tests for D1py client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from D1py import D1py
from D1py._models import D1Database, ExportResult, TimeTravelBookmark, TimeTravelRestore
from D1py.exceptions import D1APIError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACCOUNT_ID = "test-account-123"
API_TOKEN = "test-api-token-456"
DATABASE_ID = "db-uuid-789"


def _make_client(**kwargs) -> D1py:
    return D1py(ACCOUNT_ID, API_TOKEN, max_retries=1, **kwargs)


def _api_response(
    result=None,
    success=True,
    errors=None,
    result_info=None,
) -> dict:
    return {
        "success": success,
        "errors": errors or [],
        "messages": [],
        "result": result,
        "result_info": result_info,
    }


# ---------------------------------------------------------------------------
# Database CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_databases():
    client = _make_client()
    mock_resp = _api_response(
        result=[
            {"uuid": "abc", "name": "db1", "created_at": "2024-01-01T00:00:00Z"},
            {"uuid": "def", "name": "db2", "created_at": "2024-01-02T00:00:00Z"},
        ],
        result_info={"count": 2, "page": 1, "per_page": 20, "total_count": 2},
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        dbs, info = await client.list_databases()

    assert len(dbs) == 2
    assert dbs[0].uuid == "abc"
    assert dbs[0].name == "db1"
    assert dbs[1].uuid == "def"
    assert info is not None
    assert info.total_count == 2
    await client.close()


@pytest.mark.asyncio
async def test_list_databases_with_filters():
    client = _make_client()
    mock_resp = _api_response(result=[], result_info={"count": 0, "total_count": 0})

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.list_databases(name="mydb", page=2, per_page=10)

        call_args = mock.call_args
        assert call_args[1]["params"]["name"] == "mydb"
        assert call_args[1]["params"]["page"] == 2
        assert call_args[1]["params"]["per_page"] == 10
    await client.close()


@pytest.mark.asyncio
async def test_create_database():
    client = _make_client()
    mock_resp = _api_response(
        result={"uuid": "new-uuid", "name": "my-db", "created_at": "2024-01-01T00:00:00Z"}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        db = await client.create_database("my-db")

    assert isinstance(db, D1Database)
    assert db.uuid == "new-uuid"
    assert db.name == "my-db"
    await client.close()


@pytest.mark.asyncio
async def test_create_database_with_options():
    client = _make_client()
    mock_resp = _api_response(
        result={"uuid": "new-uuid", "name": "my-db", "jurisdiction": "eu"}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        db = await client.create_database(
            "my-db",
            jurisdiction="eu",
            primary_location_hint="wnam",
            read_replication_mode="auto",
        )

        call_args = mock.call_args
        payload = call_args[1]["json"]
        assert payload["name"] == "my-db"
        assert payload["jurisdiction"] == "eu"
        assert payload["primary_location_hint"] == "wnam"
        assert payload["read_replication"] == {"mode": "auto"}

    assert db.jurisdiction == "eu"
    await client.close()


@pytest.mark.asyncio
async def test_delete_database():
    client = _make_client()
    mock_resp = _api_response(result={})

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.delete_database(DATABASE_ID)

        call_args = mock.call_args
        assert call_args[0][0] == "DELETE"
        assert DATABASE_ID in call_args[0][1]
    await client.close()


@pytest.mark.asyncio
async def test_get_database():
    client = _make_client()
    mock_resp = _api_response(
        result={"uuid": DATABASE_ID, "name": "db1", "num_tables": 5, "file_size": 1024}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        db = await client.get_database(DATABASE_ID)

    assert db.uuid == DATABASE_ID
    assert db.num_tables == 5
    assert db.file_size == 1024
    await client.close()


@pytest.mark.asyncio
async def test_get_database_with_fields():
    client = _make_client()
    mock_resp = _api_response(result={"uuid": DATABASE_ID, "name": "db1"})

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.get_database(DATABASE_ID, fields=["uuid", "name"])

        call_args = mock.call_args
        assert call_args[1]["params"]["fields"] == "uuid,name"
    await client.close()


@pytest.mark.asyncio
async def test_update_database():
    client = _make_client()
    mock_resp = _api_response(
        result={"uuid": DATABASE_ID, "read_replication": {"mode": "auto"}}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        db = await client.update_database(DATABASE_ID, read_replication_mode="auto")

        call_args = mock.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[1]["json"] == {"read_replication": {"mode": "auto"}}

    assert db.read_replication == {"mode": "auto"}
    await client.close()


@pytest.mark.asyncio
async def test_patch_database():
    client = _make_client()
    mock_resp = _api_response(
        result={"uuid": DATABASE_ID, "read_replication": {"mode": "disabled"}}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.patch_database(DATABASE_ID, read_replication_mode="disabled")

        call_args = mock.call_args
        assert call_args[0][0] == "PATCH"
    await client.close()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query():
    client = _make_client()
    mock_resp = _api_response(
        result=[
            {
                "meta": {"duration": 0.5, "rows_read": 10, "rows_written": 0},
                "results": [{"id": 1, "name": "Alice"}],
                "success": True,
            }
        ]
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        results = await client.query(DATABASE_ID, "SELECT * FROM users")

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].meta is not None
    assert results[0].meta.duration == 0.5
    assert results[0].results[0]["name"] == "Alice"
    await client.close()


@pytest.mark.asyncio
async def test_query_with_params():
    client = _make_client()
    mock_resp = _api_response(
        result=[{"meta": {}, "results": [{"id": 1}], "success": True}]
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.query(
            DATABASE_ID, "SELECT * FROM users WHERE id = ?", params=["1"]
        )

        call_args = mock.call_args
        payload = call_args[1]["json"]
        assert payload["sql"] == "SELECT * FROM users WHERE id = ?"
        assert payload["params"] == ["1"]
    await client.close()


@pytest.mark.asyncio
async def test_query_batch():
    client = _make_client()
    mock_resp = _api_response(
        result=[
            {"meta": {}, "results": [], "success": True},
            {"meta": {}, "results": [], "success": True},
        ]
    )
    queries = [
        {"sql": "SELECT 1"},
        {"sql": "SELECT 2"},
    ]

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        results = await client.query_batch(DATABASE_ID, queries)

    assert len(results) == 2
    assert all(r.success for r in results)

    call_args = mock.call_args
    assert call_args[1]["json"]["batch"] == queries
    await client.close()


@pytest.mark.asyncio
async def test_raw_query():
    client = _make_client()
    mock_resp = _api_response(
        result=[
            {
                "meta": {"duration": 0.3},
                "results": {
                    "columns": ["id", "name"],
                    "rows": [[1, "Alice"], [2, "Bob"]],
                },
                "success": True,
            }
        ]
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        results = await client.raw_query(DATABASE_ID, "SELECT * FROM users")

    assert len(results) == 1
    assert results[0].results is not None
    assert results[0].results.columns == ["id", "name"]
    assert results[0].results.rows == [[1, "Alice"], [2, "Bob"]]
    await client.close()


@pytest.mark.asyncio
async def test_raw_query_batch():
    client = _make_client()
    mock_resp = _api_response(
        result=[
            {"meta": {}, "results": {"columns": ["1"], "rows": [[1]]}, "success": True},
        ]
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        results = await client.raw_query_batch(
            DATABASE_ID, [{"sql": "SELECT 1"}]
        )
    assert len(results) == 1
    await client.close()


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_database():
    client = _make_client()

    # First response: init with bookmark
    init_resp = _api_response(
        result={"at_bookmark": "bookmark-1", "status": None}
    )
    # Second response: complete
    complete_resp = _api_response(
        result={
            "status": "complete",
            "at_bookmark": "bookmark-1",
            "result": {"filename": "db.sql", "signed_url": "https://example.com/download"},
        }
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.side_effect = [
            httpx.Response(200, json=init_resp),
            httpx.Response(200, json=complete_resp),
        ]
        result = await client.export_database(DATABASE_ID)

    assert isinstance(result, ExportResult)
    assert result.status == "complete"
    assert result.result["signed_url"] == "https://example.com/download"
    await client.close()


@pytest.mark.asyncio
async def test_export_database_with_tables():
    client = _make_client()
    init_resp = _api_response(result={"at_bookmark": "b1"})
    complete_resp = _api_response(result={"status": "complete", "result": {}})

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.side_effect = [
            httpx.Response(200, json=init_resp),
            httpx.Response(200, json=complete_resp),
        ]
        await client.export_database(DATABASE_ID, tables=["users", "posts"])

        first_call = mock.call_args_list[0]
        payload = first_call[1]["json"]
        assert payload["dump_options"]["tables"] == ["users", "posts"]
    await client.close()


# ---------------------------------------------------------------------------
# Time Travel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_bookmark():
    client = _make_client()
    mock_resp = _api_response(
        result={"bookmark": "00000001-00000002-00004e2f-abc123"}
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        bm = await client.get_bookmark(DATABASE_ID)

    assert isinstance(bm, TimeTravelBookmark)
    assert bm.bookmark == "00000001-00000002-00004e2f-abc123"
    await client.close()


@pytest.mark.asyncio
async def test_get_bookmark_with_timestamp():
    client = _make_client()
    mock_resp = _api_response(result={"bookmark": "bm-ts"})

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        await client.get_bookmark(DATABASE_ID, timestamp="2024-01-01T00:00:00Z")

        call_args = mock.call_args
        assert call_args[1]["params"]["timestamp"] == "2024-01-01T00:00:00Z"
    await client.close()


@pytest.mark.asyncio
async def test_restore():
    client = _make_client()
    mock_resp = _api_response(
        result={
            "bookmark": "new-bm",
            "message": "Database restored successfully",
            "previous_bookmark": "old-bm",
        }
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        restore = await client.restore(DATABASE_ID, bookmark="old-bm")

    assert isinstance(restore, TimeTravelRestore)
    assert restore.bookmark == "new-bm"
    assert restore.previous_bookmark == "old-bm"
    await client.close()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_error_raises():
    client = _make_client()
    mock_resp = _api_response(
        success=False,
        errors=[{"code": 7500, "message": "no such column: ids"}],
    )

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        mock.return_value = httpx.Response(200, json=mock_resp)
        with pytest.raises(D1APIError) as exc_info:
            await client.query(DATABASE_ID, "SELECT ids FROM t1")

    assert "no such column" in str(exc_info.value)
    assert exc_info.value.code == 7500
    await client.close()


@pytest.mark.asyncio
async def test_http_error_raises():
    client = _make_client()

    with patch.object(client._get_client(), "request", new_callable=AsyncMock) as mock:
        error_response = {
            "success": False,
            "errors": [{"code": 1000, "message": "unauthorized"}],
        }
        mock.return_value = httpx.Response(401, json=error_response)
        with pytest.raises(D1APIError):
            await client.query(DATABASE_ID, "SELECT 1")
    await client.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_manager():
    async with D1py(ACCOUNT_ID, API_TOKEN) as client:
        assert client._get_client() is not None
    # Client should be closed after context exit
    assert client._client is not None
    assert client._client.is_closed

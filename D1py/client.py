"""D1py async client — Cloudflare D1 Python SDK."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ._models import (
    APIResponse,
    D1Database,
    ExportResult,
    ImportResult,
    QueryResult,
    RawQueryResult,
    ResultInfo,
    TimeTravelBookmark,
    TimeTravelRestore,
)
from .exceptions import D1APIError, D1Error


class D1py:
    """Async Cloudflare D1 client.

    Usage::

        async with D1py(account_id="...", api_token="...") as d1:
            dbs = await d1.list_databases()

    Or sync::

        d1 = D1py(account_id="...", api_token="...")
        dbs = d1.list_databases_sync()
    """

    BASE_URL = "https://api.cloudflare.com/client/v4/accounts"

    def __init__(
        self,
        account_id: str,
        api_token: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._account_id = account_id
        self._api_token = api_token
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"{self.BASE_URL}/{self._account_id}/d1/database",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_token}",
                },
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> D1py:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __del__(self) -> None:
        if self._client and not self._client.is_closed:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.close())
            except RuntimeError:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, data: dict[str, Any]) -> APIResponse:
        """Parse raw JSON into an APIResponse."""
        resp = APIResponse(**data)
        if not resp.success and resp.errors:
            msgs = "; ".join(
                f"[{e.code}] {e.message}" for e in resp.errors if e.message
            )
            raise D1APIError(
                msgs or "Unknown API error",
                code=resp.errors[0].code if resp.errors else None,
                errors=[e.model_dump() for e in resp.errors],
            )
        return resp

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> APIResponse:
        """Send an HTTP request with retry logic."""
        client = self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                resp = await client.request(
                    method, path, json=json, params=params
                )
                if resp.status_code >= 400:
                    try:
                        return self._parse_response(resp.json())
                    except Exception:
                        raise D1APIError(
                            f"HTTP {resp.status_code}: {resp.text}"
                        ) from None
                return self._parse_response(resp.json())
            except D1APIError:
                raise
            except httpx.RequestError as exc:
                last_exc = exc

            if attempt < self._max_retries - 1:
                await asyncio.sleep(2 ** attempt * 0.5)

        raise D1Error(
            f"Request failed after {self._max_retries} attempts",
            errors=[],
        ) from last_exc

    # ------------------------------------------------------------------
    # Database CRUD
    # ------------------------------------------------------------------

    async def list_databases(
        self,
        *,
        name: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> tuple[list[D1Database], ResultInfo | None]:
        """List all D1 databases, with optional filtering and pagination."""
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        resp = await self._request("GET", "", params=params or None)
        result = resp.result or []
        return [D1Database(**db) for db in result], resp.result_info

    async def create_database(
        self,
        name: str,
        *,
        jurisdiction: str | None = None,
        primary_location_hint: str | None = None,
        read_replication_mode: str | None = None,
    ) -> D1Database:
        """Create a new D1 database."""
        payload: dict[str, Any] = {"name": name}
        if jurisdiction is not None:
            payload["jurisdiction"] = jurisdiction
        if primary_location_hint is not None:
            payload["primary_location_hint"] = primary_location_hint
        if read_replication_mode is not None:
            payload["read_replication"] = {"mode": read_replication_mode}
        resp = await self._request("POST", "", json=payload)
        return D1Database(**(resp.result or {}))

    async def delete_database(self, database_id: str) -> None:
        """Delete a D1 database."""
        await self._request("DELETE", f"/{database_id}")

    async def get_database(
        self,
        database_id: str,
        *,
        fields: list[str] | None = None,
    ) -> D1Database:
        """Get a single D1 database."""
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = ",".join(fields)
        resp = await self._request(
            "GET", f"/{database_id}", params=params or None
        )
        return D1Database(**(resp.result or {}))

    async def update_database(
        self,
        database_id: str,
        *,
        read_replication_mode: str,
    ) -> D1Database:
        """Full update of a D1 database (PUT)."""
        payload: dict[str, Any] = {
            "read_replication": {"mode": read_replication_mode}
        }
        resp = await self._request("PUT", f"/{database_id}", json=payload)
        return D1Database(**(resp.result or {}))

    async def patch_database(
        self,
        database_id: str,
        *,
        read_replication_mode: str | None = None,
    ) -> D1Database:
        """Partial update of a D1 database (PATCH)."""
        payload: dict[str, Any] = {}
        if read_replication_mode is not None:
            payload["read_replication"] = {"mode": read_replication_mode}
        resp = await self._request("PATCH", f"/{database_id}", json=payload or None)
        return D1Database(**(resp.result or {}))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def query(
        self,
        database_id: str,
        sql: str,
        *,
        params: list[str] | None = None,
    ) -> list[QueryResult]:
        """Execute a SQL query (returns objects)."""
        payload: dict[str, Any] = {"sql": sql}
        if params is not None:
            payload["params"] = params
        resp = await self._request(
            "POST", f"/{database_id}/query", json=payload
        )
        result = resp.result or []
        return [QueryResult(**r) for r in result]

    async def query_batch(
        self,
        database_id: str,
        queries: list[dict[str, Any]],
    ) -> list[QueryResult]:
        """Execute multiple SQL queries in a batch.

        Each query dict should have ``{"sql": "...", "params": [...]}``.
        """
        payload: dict[str, Any] = {"batch": queries}
        resp = await self._request(
            "POST", f"/{database_id}/query", json=payload
        )
        result = resp.result or []
        return [QueryResult(**r) for r in result]

    async def raw_query(
        self,
        database_id: str,
        sql: str,
        *,
        params: list[str] | None = None,
    ) -> list[RawQueryResult]:
        """Execute a raw SQL query (returns column arrays + row arrays)."""
        payload: dict[str, Any] = {"sql": sql}
        if params is not None:
            payload["params"] = params
        resp = await self._request(
            "POST", f"/{database_id}/raw", json=payload
        )
        result = resp.result or []
        return [RawQueryResult(**r) for r in result]

    async def raw_query_batch(
        self,
        database_id: str,
        queries: list[dict[str, Any]],
    ) -> list[RawQueryResult]:
        """Execute multiple raw SQL queries in a batch."""
        payload: dict[str, Any] = {"batch": queries}
        resp = await self._request(
            "POST", f"/{database_id}/raw", json=payload
        )
        result = resp.result or []
        return [RawQueryResult(**r) for r in result]

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    async def export_database(
        self,
        database_id: str,
        *,
        tables: list[str] | None = None,
        no_data: bool = False,
        no_schema: bool = False,
    ) -> ExportResult:
        """Start an export and poll until complete.

        Returns the signed download URL when done.
        """
        payload: dict[str, Any] = {"output_format": "polling"}
        if tables is not None:
            payload["dump_options"] = {"tables": tables}
        elif no_data or no_schema:
            payload["dump_options"] = {}
            if no_data:
                payload["dump_options"]["no_data"] = True
            if no_schema:
                payload["dump_options"]["no_schema"] = True

        resp = await self._request(
            "POST", f"/{database_id}/export", json=payload
        )
        result_data = resp.result or {}
        bookmark = result_data.get("at_bookmark")

        # Poll until complete
        while True:
            poll_payload: dict[str, Any] = {"output_format": "polling"}
            if bookmark:
                poll_payload["current_bookmark"] = bookmark

            poll_resp = await self._request(
                "POST", f"/{database_id}/export", json=poll_payload
            )
            poll_data = poll_resp.result or {}
            status = poll_data.get("status")

            if status == "complete":
                return ExportResult(**poll_data)
            if status == "error":
                return ExportResult(**poll_data)

            bookmark = poll_data.get("at_bookmark", bookmark)
            await asyncio.sleep(1)

    async def import_database(
        self,
        database_id: str,
        sql_content: str,
    ) -> ImportResult:
        """Import SQL content into a D1 database.

        Handles the full init -> upload -> ingest -> poll flow.
        """
        import hashlib

        etag = hashlib.md5(sql_content.encode()).hexdigest()

        # Step 1: Init
        init_resp = await self._request(
            "POST",
            f"/{database_id}/import",
            json={"action": "init", "etag": etag},
        )
        init_data = init_resp.result or {}
        upload_url = init_data.get("upload_url")

        if not upload_url:
            # File already exists — skip upload
            filename = init_data.get("filename", "")
        else:
            filename = init_data.get("filename", f"{database_id}_{etag}.sql")

            # Step 2: Upload to R2 presigned URL
            async with httpx.AsyncClient() as upload_client:
                upload_resp = await upload_client.put(
                    upload_url,
                    content=sql_content.encode(),
                    headers={"Content-Type": "application/sql"},
                )
                upload_resp.raise_for_status()

        # Step 3: Ingest
        await self._request(
            "POST",
            f"/{database_id}/import",
            json={"action": "ingest", "etag": etag, "filename": filename},
        )

        # Step 4: Poll
        bookmark = init_data.get("at_bookmark")
        while True:
            poll_payload: dict[str, Any] = {"action": "poll"}
            if bookmark:
                poll_payload["current_bookmark"] = bookmark

            poll_resp = await self._request(
                "POST", f"/{database_id}/import", json=poll_payload
            )
            poll_data = poll_resp.result or {}
            status = poll_data.get("status")

            if status == "complete":
                return ImportResult(**poll_data)
            if status == "error":
                return ImportResult(**poll_data)

            bookmark = poll_data.get("at_bookmark", bookmark)
            await asyncio.sleep(1)

    # ------------------------------------------------------------------
    # Time Travel
    # ------------------------------------------------------------------

    async def get_bookmark(
        self,
        database_id: str,
        *,
        timestamp: str | None = None,
    ) -> TimeTravelBookmark:
        """Get the current (or historical) bookmark for a D1 database."""
        params: dict[str, Any] = {}
        if timestamp is not None:
            params["timestamp"] = timestamp
        resp = await self._request(
            "GET", f"/{database_id}/time_travel/bookmark", params=params or None
        )
        return TimeTravelBookmark(**(resp.result or {}))

    async def restore(
        self,
        database_id: str,
        *,
        bookmark: str | None = None,
        timestamp: str | None = None,
    ) -> TimeTravelRestore:
        """Restore a D1 database to a bookmark or timestamp."""
        params: dict[str, Any] = {}
        if bookmark is not None:
            params["bookmark"] = bookmark
        if timestamp is not None:
            params["timestamp"] = timestamp
        resp = await self._request(
            "POST", f"/{database_id}/time_travel/restore", params=params or None
        )
        return TimeTravelRestore(**(resp.result or {}))

    # ------------------------------------------------------------------
    # Sync wrappers
    # ------------------------------------------------------------------

    def _run_sync(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "Cannot call sync methods from within an async event loop. "
                "Use the async methods instead."
            )
        return asyncio.run(coro)

    def list_databases_sync(self, **kwargs: Any) -> Any:
        return self._run_sync(self.list_databases(**kwargs))

    def create_database_sync(self, name: str, **kwargs: Any) -> Any:
        return self._run_sync(self.create_database(name, **kwargs))

    def delete_database_sync(self, database_id: str) -> None:
        return self._run_sync(self.delete_database(database_id))

    def get_database_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.get_database(database_id, **kwargs))

    def update_database_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.update_database(database_id, **kwargs))

    def patch_database_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.patch_database(database_id, **kwargs))

    def query_sync(self, database_id: str, sql: str, **kwargs: Any) -> Any:
        return self._run_sync(self.query(database_id, sql, **kwargs))

    def query_batch_sync(self, database_id: str, queries: Any) -> Any:
        return self._run_sync(self.query_batch(database_id, queries))

    def raw_query_sync(self, database_id: str, sql: str, **kwargs: Any) -> Any:
        return self._run_sync(self.raw_query(database_id, sql, **kwargs))

    def raw_query_batch_sync(self, database_id: str, queries: Any) -> Any:
        return self._run_sync(self.raw_query_batch(database_id, queries))

    def export_database_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.export_database(database_id, **kwargs))

    def import_database_sync(self, database_id: str, sql_content: str) -> Any:
        return self._run_sync(self.import_database(database_id, sql_content))

    def get_bookmark_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.get_bookmark(database_id, **kwargs))

    def restore_sync(self, database_id: str, **kwargs: Any) -> Any:
        return self._run_sync(self.restore(database_id, **kwargs))

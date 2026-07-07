"""Pydantic models for Cloudflare D1 API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class D1Database(BaseModel):
    """A Cloudflare D1 database."""

    uuid: str | None = None
    name: str | None = None
    created_at: str | None = None
    version: str | None = None
    jurisdiction: str | None = None
    num_tables: int | None = None
    file_size: int | None = None
    running_in_region: str | None = None
    read_replication: dict[str, Any] | None = None


class QueryMeta(BaseModel):
    """Metadata returned by D1 query endpoints."""

    changed_db: bool | None = None
    changes: int | None = None
    duration: float | None = None
    last_row_id: int | None = None
    rows_read: int | None = None
    rows_written: int | None = None
    served_by_colo: str | None = None
    served_by_primary: bool | None = None
    served_by_region: str | None = None
    size_after: int | None = None
    timings: dict[str, Any] | None = None


class QueryResult(BaseModel):
    """Result of a single D1 query statement."""

    meta: QueryMeta | None = None
    results: Any = None
    success: bool | None = None


class RawQueryResults(BaseModel):
    """Results from the /raw endpoint — columns + rows arrays."""

    columns: list[str] | None = None
    rows: list[list[Any]] | None = None


class RawQueryResult(BaseModel):
    """Result of a single raw query statement."""

    meta: QueryMeta | None = None
    results: RawQueryResults | None = None
    success: bool | None = None


class TimeTravelBookmark(BaseModel):
    """A time-travel bookmark."""

    bookmark: str | None = None


class TimeTravelRestore(BaseModel):
    """Result of a time-travel restore operation."""

    bookmark: str | None = None
    message: str | None = None
    previous_bookmark: str | None = None


class ExportResult(BaseModel):
    """Result of an export polling response."""

    at_bookmark: str | None = None
    error: str | None = None
    messages: list[str] | None = None
    result: dict[str, Any] | None = None
    status: str | None = None
    success: bool | None = None
    type: str | None = None


class ImportResult(BaseModel):
    """Result of an import polling response."""

    at_bookmark: str | None = None
    error: str | None = None
    filename: str | None = None
    messages: list[str] | None = None
    result: dict[str, Any] | None = None
    status: str | None = None
    success: bool | None = None
    type: str | None = None
    upload_url: str | None = None


class ResultInfo(BaseModel):
    """Pagination info for list responses."""

    count: int | None = None
    page: int | None = None
    per_page: int | None = None
    total_count: int | None = None


class ResponseInfo(BaseModel):
    """Error/message info from API responses."""

    code: int | None = None
    message: str | None = None
    documentation_url: str | None = None


class APIResponse(BaseModel):
    """Base response from all D1 API endpoints."""

    success: bool = False
    errors: list[ResponseInfo] = Field(default_factory=list)
    messages: list[ResponseInfo] = Field(default_factory=list)
    result: Any = None
    result_info: ResultInfo | None = None

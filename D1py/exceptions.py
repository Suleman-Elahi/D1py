"""D1py exception hierarchy."""

from __future__ import annotations

from typing import Any


class D1Error(Exception):
    """Base exception for all D1py errors."""

    def __init__(self, message: str, *, errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.errors = errors or []


class D1APIError(D1Error):
    """Raised when the D1 API returns a non-success response."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        errors: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message, errors=errors)
        self.code = code


class D1ValidationError(D1Error):
    """Raised when request validation fails before sending."""

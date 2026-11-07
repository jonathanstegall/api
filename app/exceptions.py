from __future__ import annotations

#from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException
#from pydantic import BaseModel


class AppError(Exception):
    """Base application error class.

    All application-specific errors inherit from this.
    """
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retryable: bool = False

    def __init__(self, error_type: str, message: str, *, status_code: int = None, details: Optional[Dict[str, Any]] = None, retryable: bool = False):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        """Return dict suitable for JSON response."""
        return {
            "error": {
                "type": self.error_type,
                "status_code": self.status_code,
                "message": self.message,
                "details": self.details if self.details else None,
            }
        }


class HTTPExceptionFromAppError(HTTPException):
    """FastAPI HTTPException wrapper that converts AppError to proper HTTP status.

    Usage: `raise HTTPExceptionFromAppError(app_error)` from routers.
    """
    def __init__(self, app_error: AppError):
        if status_code is not None:
            status_code = {
                "NotFoundError": 404,
                "BadRequestError": 400,
                "ValidationError": 422,
                "ForbiddenError": 403,
                "UnauthorizedError": 401,
                "InternalServerError": 500,
                "ServiceUnavailableError": 503,
                # ExternalApiError, CacheError variants default to 502/503
            }.get(app_error.error_type, 500)
        super().__init__(
            status_code=status_code,
            detail=app_error.to_dict()
        )


# ---- Application-specific error types (service layer) ----

class ExternalApiError(AppError):
    """Error from external API call (Raindrop, Tumblr, Instapaper).

    retryable=True for transient errors (timeouts, 5xx, cache miss).
    retryable=False for permanent errors (invalid credentials, forbidden).
    """
    def __init__(self, message: str, *, external_api: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(
            error_type="ExternalApiError",
            message=message,
            details={
                "external_api": external_api,
                "status_code": status_code,
                **(details or {})
            },
            retryable=retryable
        )

class CacheError(AppError):
    """Error related to cache operations."""
    def __init__(self, message: str, *, cache_key: str | None = None, details: Optional[Dict[str, Any]] = None, retryable: bool = None):
        # Default retryable: True for read misses/temporary write failures, False for permanent write failures
        super().__init__(
            error_type="CacheError",
            message=message,
            details={
                "cache_key": cache_key,
                **(details or {})
            },
            retryable=retryable if retryable is not None else True  # default yes for reads/temporary issues
        )

class CacheMissError(CacheError):
    """Cache lookup returned no entry (expected for most reads)."""
    def __init__(self, message: str, *, cache_key: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            cache_key=cache_key,
            details=details or {},
            retryable=True  # Always retry on cache miss for reads
        )

class CacheWriteError(CacheError):
    """Cache write failed (e.g., Redis connection down, persistence issue)."""
    def __init__(self, message: str, *, cache_key: str | None = None, details: Optional[Dict[str, Any]] = None, retryable: bool = False):
        super().__init__(
            message,
            cache_key=cache_key,
            details=details or {},
            retryable=False
        )

class CacheReadError(CacheError):
    """Cache read failed (e.g., Redis response parse error, stale data)."""
    def __init__(self, message: str, *, cache_key: str | None = None, details: Optional[Dict[str, Any]] = None, retryable: bool = None):
        # Default retryable=True for read errors that may recover (e.g., transient network glitch)
        super().__init__(
            message,
            cache_key=cache_key,
            details=details or {},
            retryable=retryable if retryable is not None else True
        )

class ParamValidationError(AppError):
    """Parameter validation error at service level (business rules, not raw schema)."""
    def __init__(self, message: str, *, field: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ParamValidationError",
            message=message,
            details={"field": field} if field else {},
            retryable=False
        )

class LinkParseError(AppError):
    """Failed to parse/format link from external API response."""
    def __init__(self, message: str, *, source: str, raw_data: Any | None = None, details: Optional[Dict[str, Any]] = None, retryable: bool = True):
        super().__init__(
            error_type="LinkParseError",
            message=message,
            details={
                "source": source,
                "raw_data": raw_data,
                **(details or {})
            },
            retryable=retryable
        )

class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, message: str, *, resource_id: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="NotFoundError",
            message=message,
            details={"resource_id": resource_id} if resource_id else {},
            retryable=False
        )

class BadRequestError(AppError):
    """Bad request (invalid input)."""
    def __init__(self, message: str, *, field: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="BadRequestError",
            message=message,
            details={"field": field} if field else {},
            retryable=False
        )

class ValidationError(AppError):
    """Data validation failed at business logic level."""
    def __init__(self, message: str, *, field: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ValidationError",
            message=message,
            details={"field": field} if field else {},
            retryable=False
        )

class UnauthorizedError(AppError):
    """Authentication failed."""
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="UnauthorizedError",
            message=message,
            details=details or {},
            retryable=False
        )

class ForbiddenError(AppError):
    """Insufficient permissions."""
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ForbiddenError",
            message=message,
            details=details or {},
            retryable=False
        )

class InternalServerError(AppError):
    """Unexpected server error."""
    def __init__(self, message: str, *, traceback: str | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="InternalServerError",
            message=message,
            details={"traceback": traceback} if traceback else {},
            retryable=False
        )

class ServiceUnavailableError(AppError):
    """Backend service temporarily unavailable (cache/external API fail), retryable."""
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ServiceUnavailableError",
            message=message,
            details=details or {},
            retryable=True
        )

class ConflictError(AppError):
    """Request conflicts with current state (e.g., duplicate)."""
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="ConflictError",
            message=message,
            details=details or {},
            retryable=False
        )

class TooManyRequestsError(AppError):
    """Rate limiting exceeded."""
    def __init__(self, message: str, *, retry_after: int | None = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type="TooManyRequestsError",
            message=message,
            details={"retry_after": retry_after} if retry_after is not None else {},
            retryable=False
        )

# ---- Low-level backend exceptions (backend layer only) ----

class DatabaseError(Exception):
    """Database-related error."""
    def __init__(self, message: str, *, operation: str):
        self.message = message
        self.operation = operation

class CacheConnectionError(Exception):
    """Redis connection error."""
    def __init__(self, message: str):
        self.message = message

class ExternalApiTransportError(Exception):
    """HTTP/network transport failure for external API."""
    def __init__(self, message: str, *, url: str):
        self.message = message
        self.url = url

class ExternalApiParseError(Exception):
    """Failed to parse external API JSON response."""
    def __init__(self, message: str, raw_response: Any):
        self.message = message
        self.raw_response = raw_response

# ---- Convenience helpers ----

def raise_not_found(resource_id: str | None = None, message: str = "Resource not found") -> None:
    """Raise NotFoundError."""
    raise NotFoundError(message, resource_id=resource_id)

def raise_bad_request(message: str, field: str | None = None) -> None:
    """Raise BadRequestError."""
    raise BadRequestError(message, field=field)

def raise_validation_error(message: str, field: str | None = None) -> None:
    """Raise ValidationError."""
    raise ValidationError(message, field=field)

def raise_external_api_error(
    message: str,
    external_api: str,
    status_code: int | None = None,
    retryable: bool | None = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Raise ExternalApiError from backend or service layer."""
    raise ExternalApiError(message, external_api=external_api, status_code=status_code, details=details, retryable=retryable)

def raise_cache_miss(message: str, cache_key: str | None = None) -> None:
    """Raise CacheMissError (always retryable)."""
    raise CacheMissError(message, cache_key=cache_key)

def raise_cache_write_error(message: str, cache_key: str | None = None, details: Optional[Dict[str, Any]] = None) -> None:
    """Raise CacheWriteError (not retryable)."""
    raise CacheWriteError(message, cache_key=cache_key, details=details)

def raise_cache_read_error(message: str, cache_key: str | None = None, retryable: bool | None = None, details: Optional[Dict[str, Any]] = None) -> None:
    """Raise CacheReadError."""
    raise CacheReadError(message, cache_key=cache_key, retryable=retryable, details=details)

def raise_link_parse_error(message: str, source: str, raw_data: Any | None = None, retryable: bool | None = None, details: Optional[Dict[str, Any]] = None) -> None:
    """Raise LinkParseError."""
    raise LinkParseError(message, source=source, raw_data=raw_data, retryable=retryable, details=details)
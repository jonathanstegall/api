from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid
import time
import logging

logger = logging.getLogger(__name__)

# List of routes and methods to bypass middleware
EXCLUDED_ROUTES = [
    {"path": "/static", "methods": ["GET", "POST"]},
    {"path": "/favicon.ico", "methods": ["GET"]}
]

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context and timing"""

    async def dispatch(self, request: Request, call_next) -> Response:

        for route in EXCLUDED_ROUTES:
            if request.url.path == route["path"] and request.method in route["methods"]:
                print(f"[Middleware] Skipping middleware for {request.method} {request.url.path}")
                return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Attach to request state for use in handlers
        request.state.request_id = request_id

        # Track timing
        start_time = time.time()

        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log successful requests
            duration = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration * 1000, 2),
                    "status_code": response.status_code
                }
            )

            return response

        except Exception as exc:
            # Log exception with request context
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(exc)
                }
            )
            # Re-raise to let exception handlers process it
            raise

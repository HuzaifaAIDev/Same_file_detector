"""
Simple in-memory rate limiter (fixed window per client IP).

For a single-process deployment this is sufficient and dependency-free.
For multi-process/multi-instance production deployments, swap this for
a shared store (e.g. Redis) — the interface here is intentionally small
so that's a drop-in change.
"""
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import get_logger

security_logger = get_logger("security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        bucket = self._hits[client_ip]

        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
            security_logger.info("Rate limit exceeded for %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"success": False, "message": "Too many requests. Please slow down."},
            )

        bucket.append(now)
        return await call_next(request)

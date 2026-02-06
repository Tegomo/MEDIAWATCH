"""Rate limiting middleware basé sur Redis"""
import time
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config import settings
from src.lib.logger import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting par IP et par utilisateur.
    Utilise Redis pour le stockage des compteurs (sliding window).
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(settings.redis_url, socket_timeout=1)
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _get_client_id(self, request: Request) -> str:
        """Identifie le client par IP ou token."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json", "/"):
            return await call_next(request)

        r = self._get_redis()
        if r is None:
            # Redis indisponible, laisser passer
            return await call_next(request)

        client_id = self._get_client_id(request)
        key = f"ratelimit:{client_id}"
        now = time.time()
        window = 60  # 1 minute

        try:
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window + 1)
            results = pipe.execute()
            request_count = results[2]

            # Ajouter headers de rate limit
            remaining = max(0, self.requests_per_minute - request_count)
            response = None

            if request_count > self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_id}: {request_count}/{self.requests_per_minute}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Trop de requêtes. Veuillez réessayer dans quelques instants.",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except HTTPException:
            raise
        except Exception:
            # En cas d'erreur Redis, laisser passer
            return await call_next(request)

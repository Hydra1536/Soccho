import time
from typing import Any, Awaitable, Callable

import grpc
import pybreaker
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.grpc_client.auth_client import auth_client

UNPROTECTED_PREFIXES = (
    '/health',
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/refresh',
    '/api/auth/forgot-password',
    '/oauth/',
)


def _is_unprotected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in UNPROTECTED_PREFIXES)


class JWTValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)
        self.token_cache: dict[str, tuple[str, float]] = {}
        self.cache_ttl_seconds = 30

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]):
        if _is_unprotected(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

        try:
            response = await self.breaker.call_async(self._validate_with_auth_service, token)
            if not getattr(response, 'valid', False):
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            user_id = str(getattr(response, 'user_id', ''))
            if not user_id:
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            request.state.user_id = user_id
            self.token_cache[token] = (user_id, time.time())
            return await call_next(request)
        except (pybreaker.CircuitBreakerError, grpc.aio.AioRpcError, grpc.RpcError, TimeoutError):
            cached = self.token_cache.get(token)
            if cached is None:
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            user_id, cached_at = cached
            if time.time() - cached_at > self.cache_ttl_seconds:
                self.token_cache.pop(token, None)
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            request.state.user_id = user_id
            return await call_next(request)
        except Exception:
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

    async def _validate_with_auth_service(self, token: str):
        return await auth_client.validate_token(token)

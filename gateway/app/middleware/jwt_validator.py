import time
from typing import Any, Awaitable, Callable
import logging

import grpc
import jwt
import pybreaker
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.grpc_client.auth_client import auth_client
from app.middleware.auth_exemptions import should_skip_auth

logger = logging.getLogger(__name__)


class JWTValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)
        self.token_cache: dict[str, tuple[str, float]] = {}
        self.cache_ttl_seconds = 30
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]):
        if should_skip_auth(request.method, request.url.path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            logger.info("Auth rejected: missing token path=%s method=%s", request.url.path, request.method)
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

        try:
            response = await self.breaker.call_async(self._validate_with_auth_service, token)
            if not getattr(response, 'valid', False):
                user_id = self._validate_locally(token)
                if not user_id:
                    logger.info("Auth rejected: token invalid via gRPC+local path=%s", request.url.path)
                    return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})
                request.state.user_id = user_id
                self.token_cache[token] = (user_id, time.time())
                logger.warning("Auth fallback: accepted token via local JWT verify after gRPC invalid path=%s", request.url.path)
                return await call_next(request)

            user_id = str(getattr(response, 'user_id', ''))
            if not user_id:
                logger.info("Auth rejected: empty user_id from auth service path=%s", request.url.path)
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            request.state.user_id = user_id
            self.token_cache[token] = (user_id, time.time())
            return await call_next(request)
        except (pybreaker.CircuitBreakerError, grpc.aio.AioRpcError, grpc.RpcError, TimeoutError):
            user_id = self._validate_locally(token)
            if user_id:
                request.state.user_id = user_id
                self.token_cache[token] = (user_id, time.time())
                logger.warning("Auth fallback: accepted token via local JWT verify after gRPC error path=%s", request.url.path)
                return await call_next(request)

            cached = self.token_cache.get(token)
            if cached is None:
                logger.info("Auth rejected: no cache and local verify failed after gRPC error path=%s", request.url.path)
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            user_id, cached_at = cached
            if time.time() - cached_at > self.cache_ttl_seconds:
                self.token_cache.pop(token, None)
                logger.info("Auth rejected: cached token expired after gRPC error path=%s", request.url.path)
                return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

            request.state.user_id = user_id
            logger.warning("Auth fallback: accepted cached token after gRPC error path=%s", request.url.path)
            return await call_next(request)
        except Exception:
            logger.exception("Auth middleware exception path=%s", request.url.path)
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

    def _extract_token(self, request: Request) -> str:
        auth_header = request.headers.get('Authorization', '').strip()
        if auth_header:
            parts = auth_header.split(' ', 1)
            if len(parts) == 2:
                scheme, token = parts[0].lower(), parts[1].strip()
                if scheme in {'bearer', 'jwt', 'token'} and token:
                    return token
            return ''

        cookie_token = (request.cookies.get('access_token') or '').strip()
        if cookie_token:
            return cookie_token

        query_token = (request.query_params.get('token') or '').strip()
        if query_token:
            return query_token

        return ''

    def _validate_locally(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self.settings.auth_secret_key,
                algorithms=['HS256'],
                options={'require': ['exp', 'sub']},
            )
        except jwt.PyJWTError:
            return ''

        if payload.get('type') != 'access':
            return ''

        user_id = str(payload.get('sub', '')).strip()
        return user_id

    async def _validate_with_auth_service(self, token: str):
        return await auth_client.validate_token(token)

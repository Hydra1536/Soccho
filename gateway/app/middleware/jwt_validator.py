from typing import Awaitable, Callable
import logging

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.middleware.auth_exemptions import should_skip_auth

logger = logging.getLogger(__name__)


class JWTValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[object]]):
        if should_skip_auth(request.method, request.url.path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            logger.info("Auth rejected: missing token path=%s method=%s", request.url.path, request.method)
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

        user_id = self._validate_locally(token)
        if not user_id:
            logger.info("Auth rejected: local JWT verify failed path=%s", request.url.path)
            return JSONResponse(status_code=401, content={'detail': 'Invalid credentials'})

        request.state.user_id = user_id
        try:
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

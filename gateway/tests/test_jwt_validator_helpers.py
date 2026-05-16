from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from starlette.requests import Request

from app.middleware.jwt_validator import JWTValidationMiddleware


def _build_request(path: str = "/graphql/", headers: list[tuple[bytes, bytes]] | None = None, query_string: bytes = b""):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string,
        "headers": headers or [],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }
    return Request(scope)


def _build_access_token(secret: str, user_id: str = "123"):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_extract_token_accepts_bearer_and_jwt_prefixes():
    middleware = JWTValidationMiddleware(FastAPI())

    bearer_request = _build_request(headers=[(b"authorization", b"Bearer abc.def.ghi")])
    jwt_request = _build_request(headers=[(b"authorization", b"JWT abc.def.ghi")])

    assert middleware._extract_token(bearer_request) == "abc.def.ghi"
    assert middleware._extract_token(jwt_request) == "abc.def.ghi"


def test_extract_token_uses_query_param_fallback():
    middleware = JWTValidationMiddleware(FastAPI())
    request = _build_request(query_string=b"token=abc.def.ghi")
    assert middleware._extract_token(request) == "abc.def.ghi"


def test_validate_locally_accepts_access_token_signed_with_auth_secret():
    middleware = JWTValidationMiddleware(FastAPI())
    token = _build_access_token(middleware.settings.auth_secret_key, user_id="42")
    assert middleware._validate_locally(token) == "42"

import asyncio
import json
from types import SimpleNamespace

import httpx
from starlette.requests import Request

from app.routes import proxy


def _build_request(path: str, method: str = "GET") -> Request:
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"host", b"soccho-gateway.onrender.com")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }
    return Request(scope, receive)


def test_forward_request_returns_503_on_upstream_timeout(monkeypatch):
    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, **kwargs):
            req = httpx.Request(kwargs["method"], kwargs["url"])
            raise httpx.ConnectTimeout("connect timed out", request=req)

    monkeypatch.setattr(proxy.httpx, "AsyncClient", lambda **kwargs: TimeoutClient())

    response = asyncio.run(
        proxy._forward_request(
            "https://soccho-auth.onrender.com",
            "/oauth/google/start/",
            _build_request("/oauth/google/start/"),
            timeout_seconds=0.1,
            retry_attempts=0,
            service_name="auth",
        )
    )

    assert response.status_code == 503
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["code"] == "UPSTREAM_WARMING"
    assert payload["retryable"] is True


def test_forward_request_retries_once_for_idempotent_requests(monkeypatch):
    calls = {"count": 0}

    class FlakyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                req = httpx.Request(kwargs["method"], kwargs["url"])
                raise httpx.ReadTimeout("first attempt timed out", request=req)
            return httpx.Response(200, content=b'{"ok": true}', headers={"content-type": "application/json"})

    monkeypatch.setattr(proxy.httpx, "AsyncClient", lambda **kwargs: FlakyClient())

    response = asyncio.run(
        proxy._forward_request(
            "https://soccho-auth.onrender.com",
            "/oauth/google/start/",
            _build_request("/oauth/google/start/"),
            retry_attempts=1,
            retry_backoff_seconds=0.0,
            service_name="auth",
        )
    )

    assert calls["count"] == 2
    assert response.status_code == 200


def test_proxy_oauth_uses_oauth_timeout_profile(monkeypatch):
    captured = {}

    async def fake_forward_request(target_base, suffix, request, **kwargs):
        captured["target_base"] = target_base
        captured["suffix"] = suffix
        captured["kwargs"] = kwargs
        return proxy.Response(status_code=200, content=b"ok")

    monkeypatch.setattr(proxy, "_forward_request", fake_forward_request)
    monkeypatch.setattr(
        proxy,
        "get_settings",
        lambda: SimpleNamespace(auth_http_base_url="https://soccho-auth.onrender.com"),
    )

    response = asyncio.run(proxy.proxy_oauth(_build_request("/oauth/google/start/"), "google/start/"))

    assert response.status_code == 200
    assert captured["target_base"] == "https://soccho-auth.onrender.com"
    assert captured["suffix"] == "/oauth/google/start/"
    assert captured["kwargs"]["timeout_seconds"] == proxy.OAUTH_PROXY_TIMEOUT_SECONDS
    assert captured["kwargs"]["retry_attempts"] == proxy.OAUTH_RETRY_ATTEMPTS

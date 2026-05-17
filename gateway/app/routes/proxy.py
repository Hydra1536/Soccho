import asyncio
from typing import Dict
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_PROXY_TIMEOUT_SECONDS = 20.0
GRAPHQL_PROXY_TIMEOUT_SECONDS = 30.0
OAUTH_PROXY_TIMEOUT_SECONDS = 70.0
OAUTH_RETRY_ATTEMPTS = 1
OAUTH_RETRY_BACKOFF_SECONDS = 1.5


def _service_routes() -> Dict[str, tuple[str, str]]:
    settings = get_settings()
    return {
        'auth': (settings.auth_http_base_url, '/api/auth/'),
        'social': (settings.social_http_base_url, '/api/social/'),
        'transaction': (settings.transaction_http_base_url, '/api/transactions/'),
        'transactions': (settings.transaction_http_base_url, '/api/transactions/'),
        'notification': (settings.notification_http_base_url, '/api/notification/'),
    }


def _graphql_service_map() -> Dict[str, str]:
    settings = get_settings()
    return {
        'auth': settings.auth_http_base_url,
        'social': settings.social_http_base_url,
        'transaction': settings.transaction_http_base_url,
        'notification': settings.notification_http_base_url,
    }


def _is_idempotent(method: str) -> bool:
    return (method or "").upper() in {"GET", "HEAD", "OPTIONS"}


def _should_retry_status(status_code: int) -> bool:
    return status_code in {502, 503, 504}


def _upstream_warming_response(service_name: str) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Upstream service is waking up. Please retry in a few seconds.",
            "code": "UPSTREAM_WARMING",
            "service": service_name,
            "retryable": True,
        },
        headers={"Retry-After": "5"},
    )


async def _forward_request(
    target_base: str,
    suffix: str,
    request: Request,
    *,
    timeout_seconds: float = DEFAULT_PROXY_TIMEOUT_SECONDS,
    retry_attempts: int = 0,
    retry_backoff_seconds: float = 0.0,
    service_name: str = "unknown",
) -> Response:
    body = await request.body()
    base = target_base.rstrip('/')
    path = suffix if suffix.startswith('/') else f'/{suffix}'
    target_url = f"{base}{path}"
    query = request.url.query
    if query:
        target_url = f"{target_url}?{query}"

    headers = dict(request.headers)
    headers.pop('host', None)
    headers['x-forwarded-proto'] = request.url.scheme
    if request.headers.get('host'):
        headers['x-forwarded-host'] = request.headers['host']
    user_id = getattr(request.state, 'user_id', '')
    if user_id:
        headers['x-user-id'] = user_id

    max_attempts = max(1, retry_attempts + 1)
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                upstream = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                )
            except httpx.RequestError as exc:
                can_retry = _is_idempotent(request.method) and attempt < max_attempts
                logger.warning(
                    "Proxy upstream request error",
                    extra={
                        "method": request.method,
                        "target_url": target_url,
                        "service": service_name,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )
                if can_retry:
                    await asyncio.sleep(retry_backoff_seconds * attempt)
                    continue
                return _upstream_warming_response(service_name)

            if (
                _is_idempotent(request.method)
                and attempt < max_attempts
                and _should_retry_status(upstream.status_code)
            ):
                logger.warning(
                    "Proxy retrying transient upstream status",
                    extra={
                        "method": request.method,
                        "target_url": target_url,
                        "service": service_name,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "status_code": upstream.status_code,
                    },
                )
                await asyncio.sleep(retry_backoff_seconds * attempt)
                continue
            break

    if upstream.status_code >= 500:
        logger.error(
            "Upstream service returned 5xx",
            extra={
                "method": request.method,
                "target_url": target_url,
                "service": service_name,
                "status_code": upstream.status_code,
                "response_preview": upstream.text[:500],
            },
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get('content-type'),
    )


@router.api_route('/api/{service}/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
async def proxy_api(service: str, path: str, request: Request):
    route = _service_routes().get(service.lower())
    if not route:
        raise HTTPException(status_code=404, detail='Service route not found')

    base, upstream_prefix = route
    suffix = f'{upstream_prefix}{path}' if path else upstream_prefix
    return await _forward_request(
        base,
        suffix,
        request,
        timeout_seconds=DEFAULT_PROXY_TIMEOUT_SECONDS,
        service_name=service.lower(),
    )


@router.api_route('/oauth', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
@router.api_route('/oauth/', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
@router.api_route('/oauth/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
async def proxy_oauth(request: Request, path: str = ''):
    settings = get_settings()
    suffix = f'/oauth/{path}' if path else '/oauth/'
    return await _forward_request(
        settings.auth_http_base_url,
        suffix,
        request,
        timeout_seconds=OAUTH_PROXY_TIMEOUT_SECONDS,
        retry_attempts=OAUTH_RETRY_ATTEMPTS,
        retry_backoff_seconds=OAUTH_RETRY_BACKOFF_SECONDS,
        service_name='auth',
    )


@router.api_route('/graphql', methods=['POST', 'OPTIONS'])
@router.api_route('/graphql/', methods=['POST', 'OPTIONS'])
@router.api_route('/graphql/{path:path}', methods=['POST', 'OPTIONS'])
async def proxy_graphql(request: Request, path: str = ''):
    if request.method == 'OPTIONS':
        return Response(status_code=200)

    service_name = request.headers.get('X-Service', '').strip().lower()
    base = _graphql_service_map().get(service_name)
    if not base:
        raise HTTPException(status_code=400, detail='X-Service header is required and must be valid')

    suffix = f'/graphql/{path}' if path else '/graphql/'
    return await _forward_request(
        base,
        suffix,
        request,
        timeout_seconds=GRAPHQL_PROXY_TIMEOUT_SECONDS,
        service_name=service_name or 'unknown',
    )

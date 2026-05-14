from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.config import get_settings

router = APIRouter()


def _service_bases() -> Dict[str, str]:
    settings = get_settings()
    return {
        '/api/auth/': settings.auth_http_base_url,
        '/api/social/': settings.social_http_base_url,
        '/api/transaction/': settings.transaction_http_base_url,
        '/api/transactions/': settings.transaction_http_base_url,
        '/api/notification/': settings.notification_http_base_url,
    }


def _graphql_service_map() -> Dict[str, str]:
    settings = get_settings()
    return {
        'auth': settings.auth_http_base_url,
        'social': settings.social_http_base_url,
        'transaction': settings.transaction_http_base_url,
        'notification': settings.notification_http_base_url,
    }


async def _forward_request(target_base: str, suffix: str, request: Request) -> Response:
    body = await request.body()
    target_url = f"{target_base}{suffix}"
    query = request.url.query
    if query:
        target_url = f"{target_url}?{query}"

    headers = dict(request.headers)
    headers.pop('host', None)
    user_id = getattr(request.state, 'user_id', '')
    if user_id:
        headers['x-user-id'] = user_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get('content-type'),
    )


@router.api_route('/api/{service}/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
async def proxy_api(service: str, path: str, request: Request):
    prefix = f'/api/{service}/'
    base = _service_bases().get(prefix)
    if not base:
        raise HTTPException(status_code=404, detail='Service route not found')

    suffix = f'/{path}' if path else '/'
    return await _forward_request(base, suffix, request)


@router.post('/graphql/{path:path}')
async def proxy_graphql(path: str, request: Request):
    service_name = request.headers.get('X-Service', '').strip().lower()
    base = _graphql_service_map().get(service_name)
    if not base:
        raise HTTPException(status_code=400, detail='X-Service header is required and must be valid')

    suffix = f'/graphql/{path}' if path else '/graphql/'
    return await _forward_request(base, suffix, request)

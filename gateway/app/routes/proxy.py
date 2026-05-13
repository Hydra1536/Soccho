from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router = APIRouter()

SERVICE_BASES: Dict[str, str] = {
    '/api/auth/': 'http://auth:8001',
    '/api/social/': 'http://social:8002',
    '/api/transaction/': 'http://transaction:8003',
    '/api/notification/': 'http://notification:8004',
}

GRAPHQL_SERVICE_MAP: Dict[str, str] = {
    'auth': 'http://auth:8001',
    'social': 'http://social:8002',
    'transaction': 'http://transaction:8003',
    'notification': 'http://notification:8004',
}


async def _forward_request(target_base: str, suffix: str, request: Request) -> Response:
    body = await request.body()
    target_url = f"{target_base}{suffix}"
    query = request.url.query
    if query:
        target_url = f"{target_url}?{query}"

    headers = dict(request.headers)
    headers.pop('host', None)

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
    base = SERVICE_BASES.get(prefix)
    if not base:
        raise HTTPException(status_code=404, detail='Service route not found')

    suffix = f'/{path}' if path else '/'
    return await _forward_request(base, suffix, request)


@router.post('/graphql/{path:path}')
async def proxy_graphql(path: str, request: Request):
    service_name = request.headers.get('X-Service', '').strip().lower()
    base = GRAPHQL_SERVICE_MAP.get(service_name)
    if not base:
        raise HTTPException(status_code=400, detail='X-Service header is required and must be valid')

    suffix = f'/graphql/{path}' if path else '/graphql/'
    return await _forward_request(base, suffix, request)

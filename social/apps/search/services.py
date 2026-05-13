import json
import time
from typing import Any

import grpc
import redis
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity

from grpc_infra.clients import get_auth_client, get_transaction_client


def _redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)


def fuzzy_search_usernames(queryset, query: str):
    # pg_trgm similarity-based fuzzy search on username.
    return (
        queryset.annotate(similarity=TrigramSimilarity('username', query))
        .filter(similarity__gte=0.2)
        .order_by('-similarity', 'username')
    )


def save_search_history(user_id: str, query: str) -> None:
    key = f'search_history:{user_id}'
    payload = json.dumps({'query': query, 'ts': int(time.time())})

    client = _redis_client()
    pipe = client.pipeline()
    pipe.lpush(key, payload)
    pipe.ltrim(key, 0, 49)
    pipe.expire(key, 60 * 60 * 24)
    pipe.execute()


async def get_loyalty_score(user_id: str) -> float:
    cache_key = f'loyalty_score:{user_id}'
    client = _redis_client()

    cached = client.get(cache_key)
    if cached is not None:
        return float(cached)

    tx_client = get_transaction_client()
    try:
        response = await tx_client.GetBalanceForLoyalty(user_id)
        total_given = float(getattr(response, 'total_given', 0.0))
        total_lent = float(getattr(response, 'total_lent', 0.0))
        total_transactions = float(getattr(response, 'total_transactions', 0.0))
    except (grpc.RpcError, grpc.aio.AioRpcError, AttributeError):
        total_given = 0.0
        total_lent = 0.0
        total_transactions = 0.0

    if total_transactions <= 0:
        score = 0.0
    else:
        score = (total_given - total_lent) / total_transactions

    client.setex(cache_key, 60 * 15, str(score))
    return score


async def resolve_username(user_id: str) -> str:
    auth_client = get_auth_client()
    try:
        info = await auth_client.GetUserInfo(str(user_id))
        return getattr(info, 'username', '')
    except (grpc.RpcError, grpc.aio.AioRpcError):
        return ''


def build_user_row(user_id: str, username: str, loyalty_score: float | None) -> dict[str, Any]:
    return {
        'user_id': str(user_id),
        'username': username,
        'loyalty_score': loyalty_score,
    }

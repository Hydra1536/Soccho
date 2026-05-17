import json
import time
from typing import Any

import redis
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Sum

from django.conf import settings

from apps.search.models import SearchableTransaction, SearchableUser


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


def get_search_history(user_id: str) -> list[str]:
    key = f'search_history:{user_id}'
    return _redis_client().lrange(key, 0, 49)


def get_loyalty_score(user_id: str) -> float:
    cache_key = f'loyalty_score:{user_id}'
    client = _redis_client()

    cached = client.get(cache_key)
    if cached is not None:
        return float(cached)

    confirmed = SearchableTransaction.objects.filter(
        status=SearchableTransaction.STATUS_CONFIRMED,
        is_deleted=False,
    )
    total_given = float((confirmed.filter(lender_id=user_id).aggregate(v=Sum('amount'))['v'] or 0.0))
    total_lent = float((confirmed.filter(borrower_id=user_id).aggregate(v=Sum('amount'))['v'] or 0.0))
    total_transactions = float(
        confirmed.filter(lender_id=user_id).count() + confirmed.filter(borrower_id=user_id).count()
    )

    if total_transactions <= 0:
        score = 0.0
    else:
        score = (total_given - total_lent) / total_transactions

    client.setex(cache_key, 60 * 15, str(score))
    return score


def resolve_username(user_id: str) -> str:
    user = SearchableUser.objects.filter(id=user_id).first()
    return user.username if user is not None else ''


def build_user_row(user_id: str, username: str, loyalty_score: float | None) -> dict[str, Any]:
    return {
        'user_id': str(user_id),
        'username': username,
        'loyalty_score': loyalty_score,
    }

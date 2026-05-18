import json
import time
from typing import Any

import redis
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

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


def fallback_search_usernames(queryset, query: str):
    return queryset.filter(username__icontains=query).order_by('username')


def save_search_history(user_id: str, query: str) -> None:
    key = f'search_history:{user_id}'
    payload = json.dumps({'query': query, 'ts': int(time.time())})

    try:
        client = _redis_client()
        pipe = client.pipeline()
        pipe.lpush(key, payload)
        pipe.ltrim(key, 0, 49)
        pipe.expire(key, 60 * 60 * 24)
        pipe.execute()
    except redis.RedisError:
        # Search should still work when Redis is unavailable.
        return None


def get_search_history(user_id: str) -> list[str]:
    key = f'search_history:{user_id}'
    try:
        return _redis_client().lrange(key, 0, 49)
    except redis.RedisError:
        return []


def get_loyalty_score(user_id: str) -> float:
    cache_key = f'loyalty_score:{user_id}'
    client = None
    try:
        client = _redis_client()
        cached = client.get(cache_key)
        if cached is not None:
            return float(cached)
    except redis.RedisError:
        client = None

    try:
        involved = list(
            SearchableTransaction.objects.filter(is_deleted=False)
            .filter(Q(lender_id=user_id) | Q(borrower_id=user_id))
            .only('status', 'due_date', 'updated_at', 'borrower_id', 'lender_id')
        )
    except Exception:
        return 0.0

    total_transactions = len(involved)
    if total_transactions == 0:
        return 0.0

    confirmed = [row for row in involved if row.status == SearchableTransaction.STATUS_CONFIRMED]
    confirmed_count = len(confirmed)
    completion_rate = confirmed_count / total_transactions

    # Borrow-side on-time behavior is the strongest trust signal.
    borrow_confirmed = [row for row in confirmed if str(row.borrower_id) == str(user_id)]
    if borrow_confirmed:
        on_time_hits = 0
        for row in borrow_confirmed:
            if row.due_date is None:
                on_time_hits += 1
                continue
            if row.updated_at is not None and row.updated_at.date() <= row.due_date:
                on_time_hits += 1
        on_time_rate = on_time_hits / len(borrow_confirmed)
    else:
        on_time_rate = 0.0

    transaction_consistency = min(1.0, confirmed_count / 20.0)

    score = 100.0 * (
        0.50 * completion_rate
        + 0.35 * on_time_rate
        + 0.15 * transaction_consistency
    )
    score = max(0.0, min(100.0, score))

    if client is not None:
        try:
            client.setex(cache_key, 60 * 15, str(score))
        except redis.RedisError:
            pass
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

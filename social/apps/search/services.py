import json
import time
from typing import Any

import redis
from django.contrib.postgres.search import TrigramSimilarity
from django.db import DatabaseError

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
        active = SearchableTransaction.objects.filter(is_deleted=False)
        borrower_all = list(active.filter(borrower_id=user_id).only('status', 'due_date', 'updated_at'))
    except DatabaseError:
        return 0.0

    total_borrow_transactions = len(borrower_all)
    confirmed_borrow = [row for row in borrower_all if row.status == SearchableTransaction.STATUS_CONFIRMED]
    confirmed_borrow_count = len(confirmed_borrow)

    repayments_due = [row for row in confirmed_borrow if row.due_date is not None]
    on_time_count = sum(
        1
        for row in repayments_due
        if row.updated_at is not None and row.updated_at.date() <= row.due_date
    )

    total_confirmed_transactions = active.filter(status=SearchableTransaction.STATUS_CONFIRMED).count()

    on_time_repayment_rate = (on_time_count / len(repayments_due)) if repayments_due else 0.0
    repayment_completion_rate = (
        confirmed_borrow_count / total_borrow_transactions
        if total_borrow_transactions > 0
        else 0.0
    )
    transaction_consistency = min(1.0, total_confirmed_transactions / 20.0)

    score = 100.0 * (
        0.60 * on_time_repayment_rate
        + 0.25 * repayment_completion_rate
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

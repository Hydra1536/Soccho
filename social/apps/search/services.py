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
        queryset.annotate(similarity=TrigramSimilarity("username", query))
        .filter(similarity__gte=0.2)
        .order_by("-similarity", "username")
    )


def fallback_search_usernames(queryset, query: str):
    return queryset.filter(username__icontains=query).order_by("username")


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def soundex(value: str) -> str:
    normalized = "".join(ch for ch in value.upper() if ch.isalpha())
    if not normalized:
        return ""
    mapping = {
        **dict.fromkeys(list("BFPV"), "1"),
        **dict.fromkeys(list("CGJKQSXZ"), "2"),
        **dict.fromkeys(list("DT"), "3"),
        **dict.fromkeys(list("L"), "4"),
        **dict.fromkeys(list("MN"), "5"),
        **dict.fromkeys(list("R"), "6"),
    }
    first = normalized[0]
    encoded = []
    previous = mapping.get(first, "")
    for char in normalized[1:]:
        code = mapping.get(char, "")
        if code and code != previous:
            encoded.append(code)
        previous = code
    return f"{first}{''.join(encoded)}000"[:4]


def contextual_search_usernames(queryset, query: str, limit: int = 20):
    normalized_query = (query or "").strip().lower()
    phonetic_query = soundex(normalized_query)
    try:
        base_rows = list(
            queryset.annotate(
                similarity=TrigramSimilarity("username", normalized_query)
            )
            .filter(Q(similarity__gte=0.15) | Q(username__icontains=normalized_query))
            .order_by("-similarity", "username")[:80]
        )
    except Exception:
        base_rows = list(
            queryset.filter(username__icontains=normalized_query).order_by("username")[
                :80
            ]
        )

    if not base_rows:
        base_rows = list(queryset.order_by("username")[:80])

    scored = []
    for row in base_rows:
        username = str(row.username or "")
        normalized_name = username.lower()
        edit_distance = levenshtein_distance(normalized_query, normalized_name)
        max_len = max(len(normalized_query), len(normalized_name), 1)
        edit_score = 1.0 - (edit_distance / max_len)
        phonetic_score = (
            1.0
            if phonetic_query and phonetic_query == soundex(normalized_name)
            else 0.0
        )
        contains_score = (
            1.0 if normalized_query and normalized_query in normalized_name else 0.0
        )
        trigram_score = float(getattr(row, "similarity", 0.0) or 0.0)
        score = (
            (0.45 * edit_score)
            + (0.25 * phonetic_score)
            + (0.20 * contains_score)
            + (0.10 * trigram_score)
        )
        scored.append((score, username.lower(), row))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [row for _score, _name, row in scored[:limit]]


def save_search_history(user_id: str, query: str) -> None:
    key = f"search_history:{user_id}"
    payload = json.dumps({"query": query, "ts": int(time.time())})

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
    key = f"search_history:{user_id}"
    try:
        return _redis_client().lrange(key, 0, 49)
    except redis.RedisError:
        return []


def get_loyalty_score(user_id: str) -> float:
    cache_key = f"loyalty_score:{user_id}"
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
            .only("status", "due_date", "updated_at", "borrower_id", "lender_id")
        )
    except Exception:
        return 0.0

    total_transactions = len(involved)
    if total_transactions == 0:
        return 0.0

    confirmed = [
        row
        for row in involved
        if row.status
        in {SearchableTransaction.STATUS_AGREED, SearchableTransaction.STATUS_SETTLED}
    ]
    confirmed_count = len(confirmed)
    completion_rate = confirmed_count / total_transactions

    # Borrow-side on-time behavior is the strongest trust signal.
    borrow_confirmed = [
        row for row in confirmed if str(row.borrower_id) == str(user_id)
    ]
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
        0.50 * completion_rate + 0.35 * on_time_rate + 0.15 * transaction_consistency
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
    return user.username if user is not None else ""


def build_user_row(
    user_id: str, username: str, loyalty_score: float | None
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "username": username,
        "loyalty_score": loyalty_score,
    }


def hard_evict_user_caches(*user_ids: str) -> None:
    normalized = [str(user_id).strip() for user_id in user_ids if str(user_id).strip()]
    if not normalized:
        return
    try:
        client = _redis_client()
        keys = []
        for user_id in normalized:
            keys.extend(
                [
                    f"loyalty_score:{user_id}",
                    f"friend_list:{user_id}",
                    f"friend_requests:{user_id}",
                    f"profile_snapshot:{user_id}",
                ]
            )
        if keys:
            client.delete(*keys)
    except redis.RedisError:
        return

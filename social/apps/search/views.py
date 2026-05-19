from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search.models import SearchableUser
from apps.search.services import (
    exact_key_search_usernames,
    fallback_search_usernames,
    get_loyalty_score,
    get_search_history,
    get_transaction_totals,
    normalize_search_key,
    save_search_history,
    score_username_match,
)


def _current_user_id(request) -> str:
    user_id = str(request.headers.get('x-user-id', '')).strip()
    if user_id:
        return user_id
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return str(user.id)
    return ''


def _context_rank(username: str, raw_query: str) -> tuple[int, int]:
    user_clean = normalize_search_key(username)
    query_clean = normalize_search_key(raw_query)

    if user_clean == query_clean:
        return (0, 0)
    if user_clean.startswith(query_clean):
        return (1, len(user_clean) - len(query_clean))
    if query_clean in user_clean:
        return (2, user_clean.find(query_clean))
    return (3, 9999)


class UserSearchView(APIView):
    def get(self, request):
        user_id = _current_user_id(request)
        if not user_id:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        query = request.query_params.get('q', '').strip()
        if not query:
            return JsonResponse({'results': []})

        save_search_history(user_id, query)

        queryset = SearchableUser.objects.exclude(id=user_id)

        exact_rows = []
        try:
            exact_rows = list(exact_key_search_usernames(queryset, query)[:20])
        except Exception:
            exact_rows = []

        try:
            candidate_rows = list(queryset.filter(username__icontains=query).order_by('username')[:80])
        except Exception:
            candidate_rows = list(fallback_search_usernames(queryset, query)[:80])

        merged_by_id: dict[str, dict] = {}
        for user in exact_rows:
            merged_by_id[str(user.id)] = {
                'id': str(user.id),
                'username': user.username,
                'match_type': 'exact',
                'similarity': 1.0,
            }

        for user in candidate_rows:
            user_id_str = str(user.id)
            if user_id_str in merged_by_id:
                continue
            match_type, similarity = score_username_match(user.username, query)
            merged_by_id[user_id_str] = {
                'id': user_id_str,
                'username': user.username,
                'match_type': match_type,
                'similarity': similarity,
            }

        payload = []
        for row in merged_by_id.values():
            try:
                loyalty_score = get_loyalty_score(row['id'])
            except Exception:
                loyalty_score = 0.0

            totals = get_transaction_totals(row['id'])
            payload.append(
                {
                    'id': row['id'],
                    'user_id': row['id'],
                    'username': row['username'],
                    'match_type': row['match_type'],
                    'similarity': row['similarity'],
                    'loyalty_score': loyalty_score,
                    'total_given': totals['total_given'],
                    'total_received': totals['total_received'],
                    'total_transactions': totals['total_transactions'],
                }
            )

        payload.sort(
            key=lambda row: (
                *_context_rank(str(row.get('username') or ''), query),
                {'exact': 0, 'prefix': 1, 'substring': 2, 'phonetic': 3, 'fuzzy': 4}.get(row.get('match_type'), 4),
                -(row.get('similarity') or 0.0),
                -(row.get('loyalty_score') or 0.0),
                str(row.get('username') or '').lower(),
            )
        )
        return JsonResponse({'results': payload[:20]})


class SearchHistoryView(APIView):
    def get(self, request):
        user_id = _current_user_id(request)
        if not user_id:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'history': get_search_history(user_id)})


class LoyaltyScoreView(APIView):
    def get(self, request):
        user_id = _current_user_id(request)
        if not user_id:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            score = get_loyalty_score(user_id)
        except Exception:
            score = 0.0
        return Response({'user_id': user_id, 'loyalty_score': score}, status=status.HTTP_200_OK)

from concurrent.futures import ThreadPoolExecutor, TimeoutError

from django.db import DatabaseError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search.models import SearchableUser
from apps.search.services import (
    exact_key_search_usernames,
    fallback_search_usernames,
    fuzzy_search_usernames,
    get_loyalty_score,
    get_search_history,
    get_transaction_totals,
    normalize_search_key,
    save_search_history,
)


def _current_user_id(request) -> str:
    user_id = str(request.headers.get('x-user-id', '')).strip()
    if user_id:
        return user_id
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return str(user.id)
    return ''


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
        cleaned_query = normalize_search_key(query)

        def run_exact():
            rows = list(exact_key_search_usernames(queryset, cleaned_query)[:20])
            return [
                {
                    'id': str(user.id),
                    'username': user.username,
                    'match_type': 'exact',
                    'similarity': 1.0,
                }
                for user in rows
            ]

        def run_trigram():
            rows = list(fuzzy_search_usernames(queryset, query)[:20])
            return [
                {
                    'id': str(user.id),
                    'username': user.username,
                    'match_type': 'fuzzy',
                    'similarity': float(getattr(user, 'similarity', 0.0)),
                }
                for user in rows
            ]

        exact_matches = []
        trigram_matches = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            exact_future = pool.submit(run_exact)
            trigram_future = pool.submit(run_trigram)

            try:
                exact_matches = exact_future.result(timeout=2.0)
            except Exception:
                exact_matches = []

            try:
                trigram_matches = trigram_future.result(timeout=2.0)
            except (DatabaseError, TimeoutError, Exception):
                try:
                    fallback_rows = list(fallback_search_usernames(queryset, query)[:20])
                    trigram_matches = [
                        {
                            'id': str(user.id),
                            'username': user.username,
                            'match_type': 'fuzzy',
                            'similarity': 0.0,
                        }
                        for user in fallback_rows
                    ]
                except Exception:
                    trigram_matches = []

        merged_by_id: dict[str, dict] = {}
        for row in trigram_matches:
            merged_by_id[row['id']] = row
        for row in exact_matches:
            merged_by_id[row['id']] = row

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
                0 if row.get('match_type') == 'exact' else 1,
                -(row.get('similarity') or 0.0),
                -(row.get('loyalty_score') or 0.0),
                str(row.get('username') or '').lower(),
            )
        )
        return JsonResponse({'results': payload})


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

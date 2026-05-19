import asyncio

from asgiref.sync import sync_to_async
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
    async def get(self, request):
        user_id = _current_user_id(request)
        if not user_id:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        query = request.query_params.get('q', '').strip()
        if not query:
            return JsonResponse({'results': []})

        await sync_to_async(save_search_history, thread_sensitive=True)(user_id, query)

        queryset = SearchableUser.objects.exclude(id=user_id)
        cleaned_query = normalize_search_key(query)

        async def _run_exact():
            def _fetch():
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
            return await sync_to_async(_fetch, thread_sensitive=True)()

        async def _run_trigram():
            def _fetch():
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
            return await sync_to_async(_fetch, thread_sensitive=True)()

        # Run exact and trigram branches in parallel; tolerate branch failures.
        exact_res, trigram_res = await asyncio.gather(_run_exact(), _run_trigram(), return_exceptions=True)

        exact_matches = [] if isinstance(exact_res, Exception) else exact_res
        if isinstance(trigram_res, DatabaseError) or isinstance(trigram_res, Exception):
            def _fallback():
                rows = list(fallback_search_usernames(queryset, query)[:20])
                return [
                    {
                        'id': str(user.id),
                        'username': user.username,
                        'match_type': 'fuzzy',
                        'similarity': 0.0,
                    }
                    for user in rows
                ]
            trigram_matches = await sync_to_async(_fallback, thread_sensitive=True)()
        else:
            trigram_matches = trigram_res

        merged_by_id: dict[str, dict] = {}
        for row in trigram_matches:
            merged_by_id[row['id']] = row
        for row in exact_matches:
            merged_by_id[row['id']] = row

        merged = list(merged_by_id.values())

        payload = []
        for row in merged:
            try:
                loyalty_score = await sync_to_async(get_loyalty_score, thread_sensitive=True)(row['id'])
            except Exception:
                loyalty_score = 0.0
            payload.append(
                {
                    'id': row['id'],
                    'username': row['username'],
                    'match_type': row['match_type'],
                    'similarity': row['similarity'],
                    'loyalty_score': loyalty_score,
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

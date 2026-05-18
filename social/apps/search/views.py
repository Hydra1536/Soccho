from django.db import DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search.models import SearchableUser
from apps.search.services import (
    fallback_search_usernames,
    fuzzy_search_usernames,
    get_loyalty_score,
    get_search_history,
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
            return Response({'results': []})

        save_search_history(user_id, query)

        queryset = SearchableUser.objects.exclude(id=user_id)
        try:
            matches = list(fuzzy_search_usernames(queryset, query)[:20])
        except DatabaseError:
            matches = list(fallback_search_usernames(queryset, query)[:20])

        payload = [
            {
                'id': str(user.id),
                'username': user.username,
                'loyalty_score': get_loyalty_score(str(user.id)),
            }
            for user in matches
        ]
        payload.sort(key=lambda row: (-(row.get('loyalty_score') or 0), str(row.get('username') or '').lower()))
        return Response({'results': payload})


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
        return Response({'user_id': user_id, 'loyalty_score': get_loyalty_score(user_id)}, status=status.HTTP_200_OK)

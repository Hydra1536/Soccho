from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search.models import SearchableUser
from apps.search.services import (
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
        matches = fuzzy_search_usernames(queryset, query)[:20]

        payload = [
            {
                'id': str(user.id),
                'username': user.username,
                'loyalty_score': async_to_sync(get_loyalty_score)(str(user.id)),
            }
            for user in matches
        ]
        return Response({'results': payload})


class SearchHistoryView(APIView):
    def get(self, request):
        user_id = _current_user_id(request)
        if not user_id:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'history': get_search_history(user_id)})

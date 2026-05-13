from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search.services import fuzzy_search_usernames, save_search_history


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []})

        save_search_history(str(request.user.id), query)

        user_model = get_user_model()
        queryset = user_model.objects.exclude(id=request.user.id)
        matches = fuzzy_search_usernames(queryset, query)[:20]

        payload = [
            {'id': str(user.id), 'username': user.username}
            for user in matches
        ]
        return Response({'results': payload})

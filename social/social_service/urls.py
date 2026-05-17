from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from apps.search.views import SearchHistoryView, UserSearchView


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('api/social/', include('apps.friendships.urls')),
    path('api/social/search/', UserSearchView.as_view(), name='social-search'),
    path('api/social/search/history/', SearchHistoryView.as_view(), name='social-search-history'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=False))),
]

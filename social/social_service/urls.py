from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from graphene_django.views import GraphQLView


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('api/social/', include('apps.friendships.urls')),
    path('graphql/', GraphQLView.as_view(graphiql=False)),
]

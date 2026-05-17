from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from apps.transactions.api import api


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health/', health, name='health'),
    path('api/transactions/', api.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=False))),
]

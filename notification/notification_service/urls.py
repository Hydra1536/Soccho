from django.http import JsonResponse
from django.urls import path

from apps.notifications.views import ListNotificationsView, MarkNotificationsSeenView


def health(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health/', health, name='health'),
    path('api/notification/list/', ListNotificationsView.as_view(), name='notification-list'),
    path('api/notification/mark-seen/', MarkNotificationsSeenView.as_view(), name='notification-mark-seen'),
]

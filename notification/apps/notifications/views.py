from uuid import UUID

from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.retention import cleanup_expired_notifications, retention_cutoff
from apps.notifications.serializers import NotificationSerializer


class NotificationCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'


def _current_user_id(request) -> UUID | None:
    header_user_id = str(request.headers.get('x-user-id', '')).strip()
    if not header_user_id:
        return None
    try:
        return UUID(header_user_id)
    except ValueError:
        return None


class ListNotificationsView(APIView):
    pagination_class = NotificationCursorPagination

    def get(self, request):
        user_id = _current_user_id(request)
        if user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        cleanup_expired_notifications()
        queryset = Notification.objects.filter(
            recipient_id=user_id,
            is_cleared=False,
            created_at__gte=retention_cutoff(),
        ).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

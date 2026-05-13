import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notifications.models import Notification
from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc


class NotificationServicer(soccho_pb2_grpc.NotificationServiceServicer):
    def SendNotification(self, request, context):
        payload = {
            'title': request.title,
            'body': request.body,
            'metadata': dict(request.metadata or {}),
        }

        row = Notification.objects.create(
            recipient_id=request.user_id,
            type=Notification.TYPE_PAYMENT_ACK,
            payload=payload,
            is_cleared=False,
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{request.user_id}',
            {
                'type': 'broadcast_notification',
                'event': 'notification.push',
                'notification': {
                    'id': row.id,
                    'recipient_id': str(row.recipient_id),
                    'type': row.type,
                    'payload': row.payload,
                    'is_cleared': row.is_cleared,
                    'created_at': row.created_at.isoformat(),
                },
            },
        )

        return soccho_pb2.SendNotificationResponse(success=True, message_id=str(uuid.uuid4()), error='')

import json
from urllib.parse import parse_qs

import grpc
import jwt
import pybreaker
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from apps.notifications.models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.group_name = None
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)
        self.transaction_channel = grpc.aio.insecure_channel('transaction:8003')
        self.resolve_action_call = self.transaction_channel.unary_unary('/soccho.TransactionService/ResolveReminderAction')

    async def connect(self):
        user_id = self._extract_user_id_from_jwt()
        if not user_id:
            await self.close(code=4401)
            return

        self.user_id = user_id
        self.group_name = f'notifications_{self.user_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        pending = await self._get_pending_notifications(self.user_id)
        for row in pending:
            await self.send(text_data=json.dumps({'event': 'notification.pending', 'notification': row}))

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.transaction_channel.close()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid message'}))
            return

        action = str(payload.get('action', '')).lower()
        if action not in {'agree', 'disagree'}:
            await self.send(text_data=json.dumps({'error': 'Unsupported action'}))
            return

        notification_id = payload.get('notification_id')
        if not notification_id:
            await self.send(text_data=json.dumps({'error': 'notification_id required'}))
            return

        try:
            await self.breaker.call_async(self._call_transaction_action, action, str(notification_id))
        except Exception:
            await self.send(text_data=json.dumps({'error': 'Service Unavailable'}))
            return

        if action == 'agree':
            await self._clear_notification(str(notification_id), self.user_id)
            await self.send(text_data=json.dumps({'event': 'notification.cleared', 'notification_id': str(notification_id)}))
        else:
            await self.send(text_data=json.dumps({'event': 'notification.disagreed', 'notification_id': str(notification_id)}))

    async def broadcast_notification(self, event):
        await self.send(text_data=json.dumps({'event': event['event'], 'notification': event['notification']}))

    def _extract_user_id_from_jwt(self):
        raw_qs = self.scope.get('query_string', b'').decode('utf-8')
        token = parse_qs(raw_qs).get('token', [None])[0]
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=['HS256'])
            return str(payload.get('sub', ''))
        except jwt.PyJWTError:
            return None

    async def _call_transaction_action(self, action: str, notification_id: str):
        message = json.dumps({'action': action, 'notification_id': notification_id, 'user_id': self.user_id}).encode('utf-8')
        return await self.resolve_action_call(message)

    @database_sync_to_async
    def _get_pending_notifications(self, user_id: str):
        rows = Notification.objects.filter(recipient_id=user_id, is_cleared=False).order_by('-created_at')
        return [
            {
                'id': row.id,
                'recipient_id': str(row.recipient_id),
                'type': row.type,
                'payload': row.payload,
                'is_cleared': row.is_cleared,
                'created_at': row.created_at.isoformat(),
            }
            for row in rows
        ]

    @database_sync_to_async
    def _clear_notification(self, notification_id: str, user_id: str):
        Notification.objects.filter(id=notification_id, recipient_id=user_id).update(is_cleared=True)

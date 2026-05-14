import json
from urllib.parse import parse_qs

import httpx
import jwt
import pybreaker
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

        notification = await self._get_notification(str(notification_id), self.user_id)
        if notification is None:
            await self.send(text_data=json.dumps({'error': 'Notification not found'}))
            return

        try:
            await self.breaker.call_async(self._call_transaction_action, action, notification)
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

    async def _call_transaction_action(self, action: str, notification: dict):
        payload = notification.get('payload') or {}
        transaction_id = str(payload.get('transaction_id', '')).strip()
        borrower_id = str(payload.get('borrower_id', '')).strip()
        if not transaction_id or not borrower_id:
            raise ValueError('Notification payload is missing transaction details')

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.TRANSACTION_HTTP_BASE_URL}/api/transactions/{transaction_id}/resolve/",
                json={'action': action, 'borrower_id': borrower_id},
            )
        if response.status_code >= 400:
            raise ValueError(f'Transaction service returned {response.status_code}')
        return response.json()

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

    @database_sync_to_async
    def _get_notification(self, notification_id: str, user_id: str):
        row = Notification.objects.filter(id=notification_id, recipient_id=user_id).first()
        if row is None:
            return None
        return {
            'id': row.id,
            'recipient_id': str(row.recipient_id),
            'type': row.type,
            'payload': row.payload,
            'is_cleared': row.is_cleared,
            'created_at': row.created_at.isoformat(),
        }

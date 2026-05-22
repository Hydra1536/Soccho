import json
from urllib.parse import parse_qs

import httpx
import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from apps.notifications.models import Notification
from apps.notifications.retention import cleanup_expired_notifications, retention_cutoff


class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.group_name = None

    async def connect(self):
        await self._cleanup_expired_notifications()
        token = self._extract_token()
        if not token:
            await self.close(code=4401)
            return

        user_id = self._extract_user_id_from_jwt(token)
        if not user_id:
            user_id = await self._resolve_user_id_via_auth(token)
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
        # Notifications are intentionally read-only. Verification happens on the profile page.
        return

    async def broadcast_notification(self, event):
        await self.send(text_data=json.dumps({'event': event['event'], 'notification': event['notification']}))

    def _extract_token(self) -> str:
        raw_qs = self.scope.get('query_string', b'').decode('utf-8')
        token = parse_qs(raw_qs).get('token', [None])[0]
        if not token:
            return ''
        token = str(token).strip()
        if token.lower().startswith('bearer '):
            token = token.split(' ', 1)[1].strip()
        return token

    def _extract_user_id_from_jwt(self, token: str) -> str:
        if not token:
            return ''
        try:
            payload = jwt.decode(
                token,
                settings.AUTH_SECRET_KEY,
                algorithms=['HS256'],
                options={'require': ['exp', 'sub']},
            )
            if payload.get('type') != 'access':
                return ''
            return str(payload.get('sub', '')).strip()
        except jwt.PyJWTError:
            return ''

    async def _resolve_user_id_via_auth(self, token: str) -> str:
        if not token:
            return ''

        auth_header = token if token.lower().startswith(('bearer ', 'jwt ', 'token ')) else f'Bearer {token}'
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    f"{settings.AUTH_HTTP_BASE_URL}/api/auth/me/",
                    headers={'Authorization': auth_header},
                )
        except httpx.RequestError:
            return ''

        if response.status_code != 200:
            return ''

        try:
            payload = response.json()
        except ValueError:
            return ''

        user_id = str(payload.get('id', '')).strip()
        return user_id

    @database_sync_to_async
    def _get_pending_notifications(self, user_id: str):
        rows = Notification.objects.filter(
            recipient_id=user_id,
            is_cleared=False,
            created_at__gte=retention_cutoff(),
        ).order_by('-created_at')
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
    def _cleanup_expired_notifications(self):
        cleanup_expired_notifications()

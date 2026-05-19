import asyncio
import json
import time
from datetime import timedelta

import redis.asyncio as redis
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.retention import cleanup_expired_notifications


def _map_event_to_notification(channel: str, payload: dict):
    if channel == 'transaction.created':
        ntype = Notification.TYPE_LEND_CONFIRMATION
    elif channel == 'friend.request':
        ntype = Notification.TYPE_FRIEND_REQUEST
    elif channel == 'friend.accepted':
        ntype = Notification.TYPE_FRIEND_ACCEPTED
    elif channel in {'transaction.confirmed', 'transaction.denied'}:
        ntype = Notification.TYPE_PAYMENT_ACK
    else:
        ntype = Notification.TYPE_DUE_REMINDER

    recipient_id = payload.get('recipient_id') or payload.get('borrower_id') or payload.get('addressee_id')
    return recipient_id, ntype


@sync_to_async
def _persist_notification(recipient_id: str, ntype: str, payload: dict):
    transaction_id = str(payload.get('transaction_id', '')).strip()
    if transaction_id:
        existing = Notification.objects.filter(
            recipient_id=recipient_id,
            type=ntype,
            payload__transaction_id=transaction_id,
            created_at__gte=timezone.now() - timedelta(hours=24),
        ).first()
        if existing is not None:
            return {
                'id': existing.id,
                'recipient_id': str(existing.recipient_id),
                'type': existing.type,
                'payload': existing.payload,
                'is_cleared': existing.is_cleared,
                'is_seen': existing.is_seen,
                'seen_at': existing.seen_at.isoformat() if existing.seen_at else None,
                'created_at': existing.created_at.isoformat(),
            }

    row = Notification.objects.create(
        recipient_id=recipient_id,
        type=ntype,
        payload=payload,
        is_cleared=False,
        is_seen=False,
    )
    return {
        'id': row.id,
        'recipient_id': str(row.recipient_id),
        'type': row.type,
        'payload': row.payload,
        'is_cleared': row.is_cleared,
        'is_seen': row.is_seen,
        'seen_at': row.seen_at.isoformat() if row.seen_at else None,
        'created_at': row.created_at.isoformat(),
    }


async def run_pubsub_listener():
    client = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe('transaction.created', 'transaction.confirmed', 'transaction.denied', 'transaction.due_reminder', 'friend.request', 'friend.accepted')

    layer = get_channel_layer()
    last_cleanup_epoch = 0.0

    try:
        while True:
            now_epoch = time.time()
            if now_epoch - last_cleanup_epoch >= 600:
                await sync_to_async(cleanup_expired_notifications)()
                last_cleanup_epoch = now_epoch

            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.1)
                continue

            channel = message.get('channel')
            data = message.get('data')
            try:
                payload = json.loads(data)
            except Exception:
                continue

            recipient_id, ntype = _map_event_to_notification(channel, payload)
            if not recipient_id:
                continue

            persisted = await _persist_notification(str(recipient_id), ntype, payload)
            await layer.group_send(
                f"notifications_{recipient_id}",
                {
                    'type': 'broadcast_notification',
                    'event': channel,
                    'notification': persisted,
                },
            )
    finally:
        await pubsub.unsubscribe('transaction.created', 'transaction.confirmed', 'transaction.due_reminder', 'friend.request', 'friend.accepted')
        await pubsub.close()
        await client.close()

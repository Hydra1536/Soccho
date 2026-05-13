import json
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
import redis
from django.conf import settings

from apps.transactions.models import Transaction


def _redis_client():
    return redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)


@shared_task
def soft_delete_old_transactions():
    cutoff = timezone.now() - timedelta(days=30)
    updated = Transaction.objects.filter(
        status=Transaction.STATUS_CONFIRMED,
        is_deleted=False,
        updated_at__lt=cutoff,
    ).update(is_deleted=True)
    return updated


@shared_task
def send_due_date_reminders():
    target_date = (timezone.now() + timedelta(days=1)).date()
    rows = Transaction.objects.filter(
        is_deleted=False,
        status=Transaction.STATUS_PENDING,
        due_date=target_date,
    )

    client = _redis_client()
    count = 0
    for tx in rows:
        payload = {
            'event': 'transaction.due_reminder',
            'transaction_id': str(tx.id),
            'friendship_id': str(tx.friendship_id),
            'lender_id': str(tx.lender_id),
            'borrower_id': str(tx.borrower_id),
            'due_date': str(tx.due_date),
        }
        client.publish('transaction.due_reminder', json.dumps(payload))
        count += 1
    return count

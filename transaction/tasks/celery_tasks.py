import json
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
import redis
from django.conf import settings

from apps.transactions.models import DueRecord, Transaction, UserDirectory


def _redis_client():
    return redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)


@shared_task
def soft_delete_old_transactions():
    cutoff = timezone.now() - timedelta(days=30)
    updated = Transaction.objects.filter(
        status__in=[Transaction.STATUS_SETTLED, Transaction.STATUS_REJECTED],
        is_deleted=False,
        updated_at__lt=cutoff,
    ).update(is_deleted=True)
    return updated


@shared_task
def send_due_date_reminders():
    now = timezone.now()
    target_date = (now + timedelta(days=1)).date()
    client = _redis_client()
    count = 0
    due_soon_rows = DueRecord.objects.filter(
        status=DueRecord.STATUS_ACTIVE,
        due_date=target_date,
        due_soon_notified_at__isnull=True,
    )
    overdue_rows = DueRecord.objects.filter(
        status=DueRecord.STATUS_ACTIVE,
        due_date__lt=now.date(),
        overdue_notified_at__isnull=True,
    )

    for row in due_soon_rows:
        lender_name = _resolve_username(str(row.lender_id))
        payload = {
            'event': 'transaction.due_soon',
            'transaction_id': str(row.transaction_id),
            'friendship_id': str(row.friendship_id),
            'recipient_id': str(row.borrower_id),
            'lender_id': str(row.lender_id),
            'borrower_id': str(row.borrower_id),
            'amount': str(row.remaining_amount),
            'due_date': str(row.due_date),
            'title': 'Due soon',
            'body': f'You have a balance of {row.remaining_amount} Taka due soon for {lender_name}.',
            'route': f'/friend/{row.friendship_id}',
        }
        client.publish('transaction.due_soon', json.dumps(payload))
        DueRecord.objects.filter(id=row.id).update(due_soon_notified_at=now, updated_at=now)
        count += 1

    for row in overdue_rows:
        lender_name = _resolve_username(str(row.lender_id))
        payload = {
            'event': 'transaction.overdue',
            'transaction_id': str(row.transaction_id),
            'friendship_id': str(row.friendship_id),
            'recipient_id': str(row.borrower_id),
            'lender_id': str(row.lender_id),
            'borrower_id': str(row.borrower_id),
            'amount': str(row.remaining_amount),
            'due_date': str(row.due_date),
            'title': 'Overdue balance',
            'body': f'You have an overdue balance of {row.remaining_amount} Taka from {lender_name}.',
            'route': f'/friend/{row.friendship_id}',
        }
        client.publish('transaction.overdue', json.dumps(payload))
        DueRecord.objects.filter(id=row.id).update(overdue_notified_at=now, updated_at=now)
        count += 1
    return count


def _resolve_username(user_id: str) -> str:
    row = UserDirectory.objects.filter(id=user_id).first()
    return row.username if row is not None else 'your friend'

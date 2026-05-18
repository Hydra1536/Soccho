from datetime import timedelta

from django.utils import timezone

from apps.notifications.models import Notification

RETENTION_DAYS = 1


def retention_cutoff():
    return timezone.now() - timedelta(days=RETENTION_DAYS)


def cleanup_expired_notifications() -> int:
    deleted, _ = Notification.objects.filter(created_at__lt=retention_cutoff()).delete()
    return int(deleted or 0)

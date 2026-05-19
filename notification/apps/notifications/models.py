import uuid

from django.db import models
from django.utils import timezone


class Notification(models.Model):
    TYPE_LEND_CONFIRMATION = 'lend_confirmation'
    TYPE_PAYMENT_ACK = 'payment_ack'
    TYPE_DUE_REMINDER = 'due_reminder'
    TYPE_FRIEND_REQUEST = 'friend_request'
    TYPE_FRIEND_ACCEPTED = 'friend_accepted'

    TYPE_CHOICES = (
        (TYPE_LEND_CONFIRMATION, 'Lend Confirmation'),
        (TYPE_PAYMENT_ACK, 'Payment Acknowledgement'),
        (TYPE_DUE_REMINDER, 'Due Reminder'),
        (TYPE_FRIEND_REQUEST, 'Friend Request'),
        (TYPE_FRIEND_ACCEPTED, 'Friend Accepted'),
    )

    id = models.BigAutoField(primary_key=True)
    recipient_id = models.UUIDField(db_index=True)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    payload = models.JSONField(default=dict)
    is_cleared = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient_id', 'is_cleared', 'created_at'], name='notif_rec_clear_created_idx'),
            models.Index(fields=['recipient_id', 'is_seen', 'created_at'], name='notif_rec_seen_created_idx'),
            models.Index(fields=['type', 'created_at'], name='notif_type_created_idx'),
        ]

    @property
    def should_repeat_on_login(self) -> bool:
        return self.type == self.TYPE_DUE_REMINDER and not self.is_cleared and not self.is_seen

    def mark_seen(self) -> None:
        if self.is_seen:
            return
        self.is_seen = True
        self.seen_at = timezone.now()

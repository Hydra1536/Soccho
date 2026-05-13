import uuid

from django.db import models


class Notification(models.Model):
    TYPE_LEND_CONFIRMATION = 'lend_confirmation'
    TYPE_PAYMENT_ACK = 'payment_ack'
    TYPE_DUE_REMINDER = 'due_reminder'

    TYPE_CHOICES = (
        (TYPE_LEND_CONFIRMATION, 'Lend Confirmation'),
        (TYPE_PAYMENT_ACK, 'Payment Acknowledgement'),
        (TYPE_DUE_REMINDER, 'Due Reminder'),
    )

    id = models.BigAutoField(primary_key=True)
    recipient_id = models.UUIDField(db_index=True)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    payload = models.JSONField(default=dict)
    is_cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient_id', 'is_cleared', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]

    @property
    def should_repeat_on_login(self) -> bool:
        return self.type == self.TYPE_DUE_REMINDER and not self.is_cleared

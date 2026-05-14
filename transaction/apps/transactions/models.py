import uuid

from django.db import models
from django_cryptography.fields import encrypt


class Transaction(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DENIED = 'denied'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DENIED, 'Denied'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lender_id = models.UUIDField()
    borrower_id = models.UUIDField()
    friendship_id = models.UUIDField(db_index=True)
    amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    due_date = encrypt(models.DateField(null=True, blank=True))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    idempotency_key = models.CharField(max_length=128, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['friendship_id', 'status']),
            models.Index(fields=['borrower_id', 'status']),
            models.Index(fields=['due_date']),
        ]

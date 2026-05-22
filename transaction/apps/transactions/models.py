import uuid

from django.db import models
from django_cryptography.fields import encrypt


class Transaction(models.Model):
    STATUS_PENDING_VERIFICATION = 'pending_verification'
    STATUS_AGREED = 'agreed'
    STATUS_REJECTED = 'rejected'
    STATUS_SETTLED = 'settled'

    STATUS_CHOICES = (
        (STATUS_PENDING_VERIFICATION, 'Pending Verification'),
        (STATUS_AGREED, 'Agreed'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SETTLED, 'Settled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lender_id = models.UUIDField()
    borrower_id = models.UUIDField()
    friendship_id = models.UUIDField(db_index=True)
    friendship_route_id = models.CharField(max_length=64, blank=True, default='')
    amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    due_date = encrypt(models.DateField(null=True, blank=True))
    note = encrypt(models.TextField(blank=True, default=''))
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_VERIFICATION)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['friendship_id', 'status'], name='txn_friend_status_idx'),
            models.Index(fields=['borrower_id', 'status'], name='txn_borrower_status_idx'),
            models.Index(fields=['lender_id', 'status', 'created_at'], name='txn_lender_status_created_idx'),
            models.Index(fields=['borrower_id', 'status', 'created_at'], name='txn_borr_sts_crtd_idx'),
            models.Index(fields=['due_date'], name='txn_due_date_idx'),
        ]


class DueRecord(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_SETTLED = 'settled'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SETTLED, 'Settled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='due_record')
    lender_id = models.UUIDField()
    borrower_id = models.UUIDField()
    friendship_id = models.UUIDField(db_index=True)
    friendship_route_id = models.CharField(max_length=64, blank=True, default='')
    original_amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    remaining_amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    due_date = encrypt(models.DateField(null=True, blank=True))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    due_soon_notified_at = models.DateTimeField(null=True, blank=True)
    overdue_notified_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'due_records'
        indexes = [
            models.Index(fields=['borrower_id', 'status', 'due_date'], name='due_borrower_status_due_idx'),
            models.Index(fields=['lender_id', 'status', 'due_date'], name='due_lender_status_due_idx'),
            models.Index(fields=['friendship_id', 'status'], name='due_friend_status_idx'),
        ]


class Repayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    friendship_id = models.UUIDField(db_index=True)
    payer_id = models.UUIDField()
    payee_id = models.UUIDField()
    amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    idempotency_key = models.CharField(max_length=128, unique=True)
    note = encrypt(models.TextField(blank=True, default=''))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'repayments'
        indexes = [
            models.Index(fields=['friendship_id', 'created_at'], name='repay_friend_created_idx'),
            models.Index(fields=['payer_id', 'created_at'], name='repay_payer_created_idx'),
        ]


class UserDirectory(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    username = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'users'

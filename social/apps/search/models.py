import uuid

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django_cryptography.fields import encrypt


class SearchableUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'users'
        indexes = [
            GinIndex(
                fields=['username'],
                name='users_username_trgm_gin',
                opclasses=['gin_trgm_ops'],
            ),
        ]


class SearchableTransaction(models.Model):
    STATUS_CONFIRMED = 'confirmed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lender_id = models.UUIDField()
    borrower_id = models.UUIDField()
    amount = encrypt(models.DecimalField(max_digits=12, decimal_places=2))
    due_date = encrypt(models.DateField(null=True, blank=True))
    status = models.CharField(max_length=16)
    is_deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'transactions'

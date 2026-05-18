import uuid

from django.db import models
from django_cryptography.fields import encrypt


class SearchableUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'users'


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

import uuid

from django.db import models
from django_cryptography.fields import encrypt


class Balance(models.Model):
    id = models.BigAutoField(primary_key=True)
    friendship_id = models.UUIDField(unique=True)
    net_balance = encrypt(models.DecimalField(max_digits=14, decimal_places=2, default=0))
    version = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'balances'

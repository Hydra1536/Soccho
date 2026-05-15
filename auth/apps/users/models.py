import uuid
from hashlib import sha256

from django.db import models
from django_cryptography.fields import encrypt


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def make_email_lookup(value: str) -> str:
    normalized = normalize_email(value)
    return sha256(normalized.encode("utf-8")).hexdigest()


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = encrypt(models.EmailField(unique=True))
    email_lookup = models.CharField(max_length=64, unique=True, db_index=True)
    username = models.CharField(max_length=30, unique=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def save(self, *args, **kwargs):
        normalized_email = normalize_email(self.email)
        self.email = normalized_email
        self.email_lookup = make_email_lookup(normalized_email)
        return super().save(*args, **kwargs)


class RefreshToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"

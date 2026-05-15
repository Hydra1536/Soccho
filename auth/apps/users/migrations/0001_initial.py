import django_cryptography.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", django_cryptography.fields.encrypt(models.EmailField(max_length=254, unique=True))),
                ("username", models.CharField(max_length=30, unique=True)),
                ("password_hash", models.CharField(blank=True, max_length=255, null=True)),
                ("google_sub", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "users",
            },
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("token_hash", models.CharField(max_length=128, unique=True)),
                ("is_revoked", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_tokens",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "db_table": "refresh_tokens",
            },
        ),
    ]

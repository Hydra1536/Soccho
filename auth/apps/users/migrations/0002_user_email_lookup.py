from hashlib import sha256

from django.db import migrations, models


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _email_lookup(value: str) -> str:
    normalized = _normalize_email(value)
    return sha256(normalized.encode("utf-8")).hexdigest()


def _backfill_email_lookup(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.all().iterator():
        normalized_email = _normalize_email(user.email)
        user.email = normalized_email
        user.email_lookup = _email_lookup(normalized_email)
        user.save(update_fields=["email", "email_lookup"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_lookup",
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True, unique=True),
        ),
        migrations.RunPython(_backfill_email_lookup, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="email_lookup",
            field=models.CharField(db_index=True, max_length=64, unique=True),
        ),
    ]

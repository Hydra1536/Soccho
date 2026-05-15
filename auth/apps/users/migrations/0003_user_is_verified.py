from django.db import migrations, models


def _mark_existing_users_verified(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(is_verified=False).update(is_verified=True)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_email_lookup"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(_mark_existing_users_verified, migrations.RunPython.noop),
    ]

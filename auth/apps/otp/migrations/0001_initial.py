from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OTPCode",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("code_hash", models.CharField(max_length=128)),
                (
                    "context",
                    models.CharField(
                        choices=[
                            ("register", "Register"),
                            ("forgot", "Forgot password"),
                            ("change_pw", "Change password"),
                        ],
                        max_length=20,
                    ),
                ),
                ("expires_at", models.DateTimeField()),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otp_codes",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "db_table": "otp_codes",
            },
        ),
    ]

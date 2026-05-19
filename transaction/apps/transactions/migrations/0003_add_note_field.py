import django_cryptography.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0002_add_dashboard_loyalty_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="note",
            field=django_cryptography.fields.encrypt(models.TextField(blank=True, null=True)),
        ),
    ]

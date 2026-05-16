import django_cryptography.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('friendship_id', models.UUIDField(unique=True)),
                ('net_balance', django_cryptography.fields.encrypt(models.DecimalField(decimal_places=2, default=0, max_digits=14))),
                ('version', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'balances',
            },
        ),
    ]

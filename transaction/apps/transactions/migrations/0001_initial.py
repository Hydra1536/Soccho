import uuid

import django_cryptography.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lender_id', models.UUIDField()),
                ('borrower_id', models.UUIDField()),
                ('friendship_id', models.UUIDField(db_index=True)),
                ('amount', django_cryptography.fields.encrypt(models.DecimalField(decimal_places=2, max_digits=12))),
                ('due_date', django_cryptography.fields.encrypt(models.DateField(blank=True, null=True))),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('denied', 'Denied')], default='pending', max_length=16)),
                ('idempotency_key', models.CharField(max_length=128, unique=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'transactions',
                'indexes': [
                    models.Index(fields=['friendship_id', 'status'], name='txn_friend_status_idx'),
                    models.Index(fields=['borrower_id', 'status'], name='txn_borrower_status_idx'),
                    models.Index(fields=['due_date'], name='txn_due_date_idx'),
                ],
            },
        ),
    ]

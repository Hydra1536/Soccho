import uuid
from decimal import Decimal

import django_cryptography.fields
from django.db import migrations, models
import django.db.models.deletion


def forward_populate_due_records(apps, schema_editor):
    Transaction = apps.get_model('transactions', 'Transaction')
    DueRecord = apps.get_model('transactions', 'DueRecord')

    status_map = {
        'pending': 'pending_verification',
        'confirmed': 'agreed',
        'denied': 'rejected',
    }
    for old, new in status_map.items():
        Transaction.objects.filter(status=old).update(status=new)

    agreed_rows = Transaction.objects.filter(status='agreed', is_deleted=False)
    for tx in agreed_rows.iterator():
        amount = Decimal(tx.amount or 0)
        if amount <= 0:
            continue
        DueRecord.objects.get_or_create(
            transaction_id=tx.id,
            defaults={
                'lender_id': tx.lender_id,
                'borrower_id': tx.borrower_id,
                'friendship_id': tx.friendship_id,
                'friendship_route_id': getattr(tx, 'friendship_route_id', ''),
                'original_amount': amount,
                'remaining_amount': amount,
                'due_date': tx.due_date,
                'status': 'active',
                'settled_at': None,
            },
        )


def backward_cleanup_due_records(apps, schema_editor):
    DueRecord = apps.get_model('transactions', 'DueRecord')
    DueRecord.objects.all().delete()

    Transaction = apps.get_model('transactions', 'Transaction')
    status_map = {
        'pending_verification': 'pending',
        'agreed': 'confirmed',
        'rejected': 'denied',
        'settled': 'confirmed',
    }
    for old, new in status_map.items():
        Transaction.objects.filter(status=old).update(status=new)


def conditionally_add_note_field(apps, schema_editor):
    """Check if note field exists before adding it to handle idempotency."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='transactions' AND column_name='note'
            )
        """)
        note_exists = cursor.fetchone()[0]
        
        if note_exists:
            return  # Field already exists, skip adding it
        
        # Field doesn't exist, add it using the schema_editor
        Transaction = apps.get_model('transactions', 'Transaction')
        schema_editor.add_field(
            Transaction,
            Transaction._meta.get_field('note')
        )


class Migration(migrations.Migration):
    dependencies = [
        ('transactions', '0002_add_dashboard_loyalty_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='friendship_route_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        # Use RunPython for the note field to make it idempotent
        migrations.RunPython(conditionally_add_note_field, migrations.RunPython.noop),
        migrations.AddField(
            model_name='transaction',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending_verification', 'Pending Verification'),
                    ('agreed', 'Agreed'),
                    ('rejected', 'Rejected'),
                    ('settled', 'Settled'),
                ],
                default='pending_verification',
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name='DueRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lender_id', models.UUIDField()),
                ('borrower_id', models.UUIDField()),
                ('friendship_id', models.UUIDField(db_index=True)),
                ('friendship_route_id', models.CharField(blank=True, default='', max_length=64)),
                ('original_amount', django_cryptography.fields.encrypt(models.DecimalField(decimal_places=2, max_digits=12))),
                ('remaining_amount', django_cryptography.fields.encrypt(models.DecimalField(decimal_places=2, max_digits=12))),
                ('due_date', django_cryptography.fields.encrypt(models.DateField(blank=True, null=True))),
                ('status', models.CharField(choices=[('active', 'Active'), ('settled', 'Settled')], default='active', max_length=16)),
                ('due_soon_notified_at', models.DateTimeField(blank=True, null=True)),
                ('overdue_notified_at', models.DateTimeField(blank=True, null=True)),
                ('settled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'transaction',
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='due_record', to='transactions.transaction'),
                ),
            ],
            options={
                'db_table': 'due_records',
                'indexes': [
                    models.Index(fields=['borrower_id', 'status', 'due_date'], name='due_borrower_status_due_idx'),
                    models.Index(fields=['lender_id', 'status', 'due_date'], name='due_lender_status_due_idx'),
                    models.Index(fields=['friendship_id', 'status'], name='due_friend_status_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Repayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('friendship_id', models.UUIDField(db_index=True)),
                ('payer_id', models.UUIDField()),
                ('payee_id', models.UUIDField()),
                ('amount', django_cryptography.fields.encrypt(models.DecimalField(decimal_places=2, max_digits=12))),
                ('idempotency_key', models.CharField(max_length=128, unique=True)),
                ('note', django_cryptography.fields.encrypt(models.TextField(blank=True, default=''))),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'repayments',
                'indexes': [
                    models.Index(fields=['friendship_id', 'created_at'], name='repay_friend_created_idx'),
                    models.Index(fields=['payer_id', 'created_at'], name='repay_payer_created_idx'),
                ],
            },
        ),
        migrations.RunPython(forward_populate_due_records, backward_cleanup_due_records),
    ]

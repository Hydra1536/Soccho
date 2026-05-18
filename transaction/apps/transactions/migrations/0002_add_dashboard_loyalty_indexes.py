from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['lender_id', 'status', 'created_at'], name='txn_lender_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['borrower_id', 'status', 'created_at'], name='txn_borr_sts_crtd_idx'),
        ),
    ]

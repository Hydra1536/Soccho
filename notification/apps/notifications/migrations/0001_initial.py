from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('recipient_id', models.UUIDField(db_index=True)),
                ('type', models.CharField(choices=[('lend_confirmation', 'Lend Confirmation'), ('payment_ack', 'Payment Acknowledgement'), ('due_reminder', 'Due Reminder')], max_length=32)),
                ('payload', models.JSONField(default=dict)),
                ('is_cleared', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'notifications',
                'indexes': [
                    models.Index(fields=['recipient_id', 'is_cleared', 'created_at']),
                    models.Index(fields=['type', 'created_at']),
                ],
            },
        ),
    ]

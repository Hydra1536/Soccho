from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0002_add_friend_request_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[
                    ('lend_confirmation', 'Lend Confirmation'),
                    ('payment_ack', 'Payment Acknowledgement'),
                    ('due_reminder', 'Due Reminder'),
                    ('friend_request', 'Friend Request'),
                    ('friend_accepted', 'Friend Accepted'),
                ],
                max_length=32,
            ),
        ),
    ]

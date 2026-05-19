from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0003_add_friend_accepted_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='is_seen',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='notification',
            name='seen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient_id', 'is_seen', 'created_at'], name='notif_rec_seen_created_idx'),
        ),
    ]

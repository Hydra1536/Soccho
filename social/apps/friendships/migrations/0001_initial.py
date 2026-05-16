import uuid

from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Greatest, Least


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Friendship',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('requester_id', models.UUIDField(default=uuid.uuid4)),
                ('addressee_id', models.UUIDField(default=uuid.uuid4)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'friendships',
                'indexes': [
                    models.Index(fields=['requester_id', 'status']),
                    models.Index(fields=['addressee_id', 'status']),
                    models.Index(fields=['created_at']),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        Least(F('requester_id'), F('addressee_id')),
                        Greatest(F('requester_id'), F('addressee_id')),
                        name='uniq_friendship_pair_any_direction',
                    ),
                    models.CheckConstraint(
                        check=~models.Q(requester_id=F('addressee_id')),
                        name='check_friendship_not_self',
                    ),
                ],
            },
        ),
    ]

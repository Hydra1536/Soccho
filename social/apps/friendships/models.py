import uuid

from django.db import models
from django.db.models import F
from django.db.models.functions import Greatest, Least


class Friendship(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    )

    id = models.BigAutoField(primary_key=True)
    requester_id = models.UUIDField(default=uuid.uuid4)
    addressee_id = models.UUIDField(default=uuid.uuid4)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'friendships'
        constraints = [
            models.UniqueConstraint(
                Least(F('requester_id'), F('addressee_id')),
                Greatest(F('requester_id'), F('addressee_id')),
                name='uniq_friendship_pair_any_direction',
            ),
            models.CheckConstraint(
                check=~models.Q(requester_id=F('addressee_id')),
                name='check_friendship_not_self',
            ),
        ]
        indexes = [
            models.Index(fields=['requester_id', 'status'], name='friend_req_status_idx'),
            models.Index(fields=['addressee_id', 'status'], name='friend_addr_status_idx'),
            models.Index(fields=['created_at'], name='friend_created_idx'),
        ]

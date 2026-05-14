import uuid

from django.db import models


class SearchableUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'users'

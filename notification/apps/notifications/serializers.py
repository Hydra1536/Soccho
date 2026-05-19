from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient_id', 'type', 'payload', 'is_cleared', 'is_seen', 'seen_at', 'created_at']

from rest_framework import serializers

from apps.friendships.models import Friendship


class FriendshipActionSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = ['id', 'requester_id', 'addressee_id', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

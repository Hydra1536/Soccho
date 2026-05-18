from uuid import UUID

import json
import redis
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.friendships.models import Friendship
from apps.friendships.serializers import FriendshipActionSerializer, FriendshipSerializer
from apps.search.models import SearchableUser


class FriendshipCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'


def _current_user_id(request) -> UUID | None:
    header_user_id = str(request.headers.get('x-user-id', '')).strip()
    if header_user_id:
        try:
            return UUID(header_user_id)
        except ValueError:
            return None

    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        try:
            return UUID(str(user.id))
        except ValueError:
            return None
    return None


def _find_friendship_pair(user_a: UUID, user_b: UUID) -> Friendship | None:
    return Friendship.objects.filter(
        Q(requester_id=user_a, addressee_id=user_b) | Q(requester_id=user_b, addressee_id=user_a)
    ).first()


def _usernames_for_ids(user_ids: set[str]) -> dict[str, str]:
    if not user_ids:
        return {}
    return {
        str(user_id): username
        for user_id, username in SearchableUser.objects.filter(id__in=user_ids).values_list('id', 'username')
    }


def _username_for_user_id(user_id: UUID) -> str:
    row = SearchableUser.objects.filter(id=user_id).first()
    return row.username if row is not None else ''


def _emit_friend_request_notification(friendship: Friendship):
    payload = {
        'recipient_id': str(friendship.addressee_id),
        'requester_id': str(friendship.requester_id),
        'friendship_id': str(friendship.id),
        'title': 'New friend request',
        'body': f"{_username_for_user_id(friendship.requester_id) or 'Someone'} sent you a friend request",
    }
    try:
        client = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)
        client.publish('friend.request', json.dumps(payload))
        client.close()
    except redis.RedisError:
        return


def _idempotent_friendship_response(friendship: Friendship, requester_id: UUID, addressee_id: UUID):
    if friendship.status == Friendship.STATUS_ACCEPTED:
        return Response(
            {
                'detail': 'You are already friends',
                'friendship': FriendshipSerializer(friendship).data,
            },
            status=status.HTTP_200_OK,
        )

    if friendship.status == Friendship.STATUS_PENDING:
        if friendship.requester_id == requester_id:
            detail = 'Friend request already sent'
        else:
            detail = 'This user has already sent you a friend request'
        return Response(
            {
                'detail': detail,
                'friendship': FriendshipSerializer(friendship).data,
            },
            status=status.HTTP_200_OK,
        )

    if friendship.status == Friendship.STATUS_REJECTED:
        friendship.requester_id = requester_id
        friendship.addressee_id = addressee_id
        friendship.status = Friendship.STATUS_PENDING
        friendship.save(update_fields=['requester_id', 'addressee_id', 'status', 'updated_at'])
        _emit_friend_request_notification(friendship)
        return Response(
            {
                'detail': 'Friend request sent',
                'friendship': FriendshipSerializer(friendship).data,
            },
            status=status.HTTP_200_OK,
        )

    return Response({'detail': 'Friendship already exists'}, status=status.HTTP_409_CONFLICT)


class SendRequestView(APIView):
    def post(self, request):
        serializer = FriendshipActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requester_id = _current_user_id(request)
        if requester_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        addressee_id = serializer.validated_data['user_id']
        if requester_id == addressee_id:
            return Response({'detail': 'Cannot send friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        existing = _find_friendship_pair(requester_id, addressee_id)
        if existing is not None:
            return _idempotent_friendship_response(existing, requester_id, addressee_id)

        try:
            friendship = Friendship.objects.create(
                requester_id=requester_id,
                addressee_id=addressee_id,
                status=Friendship.STATUS_PENDING,
            )
        except IntegrityError:
            existing = _find_friendship_pair(requester_id, addressee_id)
            if existing is not None:
                return _idempotent_friendship_response(existing, requester_id, addressee_id)
            return Response({'detail': 'Friendship already exists'}, status=status.HTTP_409_CONFLICT)

        _emit_friend_request_notification(friendship)
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED)


class AcceptRequestView(APIView):
    def post(self, request):
        serializer = FriendshipActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_user_id = _current_user_id(request)
        if current_user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        requester_id = serializer.validated_data['user_id']

        friendship = Friendship.objects.filter(
            requester_id=requester_id,
            addressee_id=current_user_id,
            status=Friendship.STATUS_PENDING,
        ).first()

        if friendship is None:
            return Response({'detail': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

        friendship.status = Friendship.STATUS_ACCEPTED
        friendship.save(update_fields=['status', 'updated_at'])
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_200_OK)


class RejectRequestView(APIView):
    def post(self, request):
        serializer = FriendshipActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_user_id = _current_user_id(request)
        if current_user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        requester_id = serializer.validated_data['user_id']

        friendship = Friendship.objects.filter(
            requester_id=requester_id,
            addressee_id=current_user_id,
            status=Friendship.STATUS_PENDING,
        ).first()

        if friendship is None:
            return Response({'detail': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

        friendship.status = Friendship.STATUS_REJECTED
        friendship.save(update_fields=['status', 'updated_at'])
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_200_OK)


class ListFriendsView(APIView):
    pagination_class = FriendshipCursorPagination

    def get(self, request):
        user_id = _current_user_id(request)
        if user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        queryset = Friendship.objects.filter(
            Q(requester_id=user_id) | Q(addressee_id=user_id),
            status=Friendship.STATUS_ACCEPTED,
        ).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = FriendshipSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListPendingRequestsView(APIView):
    def get(self, request):
        user_id = _current_user_id(request)
        if user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        incoming = list(
            Friendship.objects.filter(
                addressee_id=user_id,
                status=Friendship.STATUS_PENDING,
            ).order_by('-created_at')
        )
        outgoing = list(
            Friendship.objects.filter(
                requester_id=user_id,
                status=Friendship.STATUS_PENDING,
            ).order_by('-created_at')
        )

        counterpart_ids = {str(row.requester_id) for row in incoming} | {str(row.addressee_id) for row in outgoing}
        usernames = _usernames_for_ids(counterpart_ids)

        incoming_payload = []
        for row in incoming:
            serialized = FriendshipSerializer(row).data
            serialized['counterpart_id'] = str(row.requester_id)
            serialized['counterpart_username'] = usernames.get(str(row.requester_id), '')
            incoming_payload.append(serialized)

        outgoing_payload = []
        for row in outgoing:
            serialized = FriendshipSerializer(row).data
            serialized['counterpart_id'] = str(row.addressee_id)
            serialized['counterpart_username'] = usernames.get(str(row.addressee_id), '')
            outgoing_payload.append(serialized)

        return Response({'incoming': incoming_payload, 'outgoing': outgoing_payload}, status=status.HTTP_200_OK)


class UnfriendView(APIView):
    def post(self, request):
        serializer = FriendshipActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_user_id = _current_user_id(request)
        if current_user_id is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        target_user_id = serializer.validated_data['user_id']
        if current_user_id == target_user_id:
            return Response({'detail': 'Cannot unfriend yourself'}, status=status.HTTP_400_BAD_REQUEST)

        friendship = Friendship.objects.filter(
            Q(requester_id=current_user_id, addressee_id=target_user_id)
            | Q(requester_id=target_user_id, addressee_id=current_user_id),
            status=Friendship.STATUS_ACCEPTED,
        ).first()
        if friendship is None:
            return Response({'detail': 'Friendship not found'}, status=status.HTTP_404_NOT_FOUND)

        friendship.delete()
        return Response({'detail': 'Unfriended successfully'}, status=status.HTTP_200_OK)

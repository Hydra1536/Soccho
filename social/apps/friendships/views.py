from uuid import UUID

from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.friendships.models import Friendship
from apps.friendships.serializers import FriendshipActionSerializer, FriendshipSerializer


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

        try:
            friendship = Friendship.objects.create(
                requester_id=requester_id,
                addressee_id=addressee_id,
                status=Friendship.STATUS_PENDING,
            )
        except IntegrityError:
            return Response({'detail': 'Friendship already exists'}, status=status.HTTP_409_CONFLICT)

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

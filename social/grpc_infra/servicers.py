from asgiref.sync import async_to_sync
from django.db.models import Q

from apps.friendships.models import Friendship
from grpc_infra.clients import get_auth_client
from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc


class SocialServicer(soccho_pb2_grpc.SocialServiceServicer):
    def CheckFriendship(self, request, context):
        exists = Friendship.objects.filter(
            (
                Q(requester_id=request.user_id, addressee_id=request.friend_id)
                | Q(requester_id=request.friend_id, addressee_id=request.user_id)
            ),
            status=Friendship.STATUS_ACCEPTED,
        ).exists()
        return soccho_pb2.CheckFriendshipResponse(is_friend=bool(exists))

    def GetFriendList(self, request, context):
        user_id = request.user_id
        auth_client = get_auth_client()

        friendships = Friendship.objects.filter(
            Q(requester_id=user_id) | Q(addressee_id=user_id),
            status=Friendship.STATUS_ACCEPTED,
        ).order_by('-created_at')

        friend_rows = []
        for row in friendships:
            friend_id = row.addressee_id if str(row.requester_id) == str(user_id) else row.requester_id
            info = async_to_sync(auth_client.GetUserInfo)(str(friend_id))
            friend_rows.append(
                soccho_pb2.Friend(
                    user_id=str(friend_id),
                    username=getattr(info, 'username', ''),
                )
            )

        return soccho_pb2.GetFriendListResponse(friends=friend_rows)

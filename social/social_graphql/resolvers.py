from asgiref.sync import async_to_sync
from django.db.models import Q
from promise import Promise
from promise.dataloader import DataLoader

import graphene
from apps.friendships.models import Friendship
from apps.search.services import get_loyalty_score
from grpc_infra.clients import get_auth_client
from .types import FriendNode


class UsernameLoader(DataLoader):
    def batch_load_fn(self, keys):
        auth_client = get_auth_client()

        async def _load():
            values = []
            for user_id in keys:
                info = await auth_client.GetUserInfo(str(user_id))
                values.append(getattr(info, 'username', ''))
            return values

        return Promise.resolve(async_to_sync(_load)())


class FriendListQuery(graphene.ObjectType):
    friend_list = graphene.List(FriendNode)

    def resolve_friend_list(self, info):
        request = info.context
        user_id = str(request.headers.get('x-user-id', '')).strip()
        if not user_id and hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
            user_id = str(request.user.id)
        if not user_id:
            return []

        queryset = (
            Friendship.objects.select_related()
            .prefetch_related()
            .filter(Q(requester_id=user_id) | Q(addressee_id=user_id), status=Friendship.STATUS_ACCEPTED)
            .order_by('-created_at')
        )

        loader = UsernameLoader()
        loyalty_score = async_to_sync(get_loyalty_score)(user_id)

        rows = []
        for edge in queryset:
            friend_id = edge.addressee_id if str(edge.requester_id) == user_id else edge.requester_id
            username = loader.load(str(friend_id)).get()
            rows.append(
                FriendNode(
                    friendship_id=str(edge.id),
                    requester_id=edge.requester_id,
                    addressee_id=edge.addressee_id,
                    status=edge.status,
                    created_at=edge.created_at.isoformat(),
                    user_id=friend_id,
                    username=username,
                    loyalty_score=loyalty_score,
                )
            )
        return rows

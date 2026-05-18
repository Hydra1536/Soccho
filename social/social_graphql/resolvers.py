from django.db.models import Q

import graphene
from apps.friendships.models import Friendship
from apps.search.models import SearchableUser
from apps.search.services import get_loyalty_score
from .types import FriendNode


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

        friend_ids = {
            str(edge.addressee_id if str(edge.requester_id) == user_id else edge.requester_id)
            for edge in queryset
        }
        usernames = {
            str(user_id_value): username
            for user_id_value, username in SearchableUser.objects.filter(id__in=friend_ids).values_list('id', 'username')
        }
        rows = []
        for edge in queryset:
            friend_id = edge.addressee_id if str(edge.requester_id) == user_id else edge.requester_id
            username = usernames.get(str(friend_id), '')
            try:
                loyalty_score = get_loyalty_score(str(friend_id))
            except Exception:
                loyalty_score = 0.0
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

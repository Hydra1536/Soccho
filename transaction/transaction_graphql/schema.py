import graphene

from .resolvers import (
    DashboardSummaryType,
    FriendLedgerType,
    resolve_dashboard_summary,
    resolve_friend_ledger,
)


class Query(graphene.ObjectType):
    friend_ledger = graphene.Field(FriendLedgerType, friendship_id=graphene.UUID(required=True))
    dashboard_summary = graphene.Field(DashboardSummaryType, user_id=graphene.UUID(required=True))

    async def resolve_friend_ledger(self, info, friendship_id):
        return await resolve_friend_ledger(self, info, friendship_id)

    async def resolve_dashboard_summary(self, info, user_id):
        return await resolve_dashboard_summary(self, info, user_id)


schema = graphene.Schema(query=Query)

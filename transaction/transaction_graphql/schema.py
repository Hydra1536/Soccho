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

    def resolve_friend_ledger(self, info, friendship_id):
        return resolve_friend_ledger(self, info, friendship_id)

    def resolve_dashboard_summary(self, info, user_id):
        return resolve_dashboard_summary(self, info, user_id)


schema = graphene.Schema(query=Query)

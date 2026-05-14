import graphene

from .resolvers import FriendListQuery


class Query(FriendListQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)

import graphene

from graphql.resolvers import FriendListQuery


class Query(FriendListQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)

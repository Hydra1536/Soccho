import graphene


class FriendNode(graphene.ObjectType):
    user_id = graphene.UUID(required=True)
    username = graphene.String(required=True)
    loyalty_score = graphene.Float()

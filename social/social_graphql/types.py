import graphene


class FriendNode(graphene.ObjectType):
    friendship_id = graphene.String(required=True)
    requester_id = graphene.UUID(required=True)
    addressee_id = graphene.UUID(required=True)
    status = graphene.String(required=True)
    created_at = graphene.String(required=True)
    user_id = graphene.UUID(required=True)
    username = graphene.String(required=True)
    loyalty_score = graphene.Float()
    total_given = graphene.Float()
    total_received = graphene.Float()
    total_transactions = graphene.Int()

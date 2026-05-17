from decimal import Decimal

import graphene
from django.db.models import Q, Sum

from apps.balances.models import Balance
from apps.transactions.models import Transaction


class LedgerEntryType(graphene.ObjectType):
    id = graphene.UUID()
    lender_id = graphene.UUID()
    borrower_id = graphene.UUID()
    friendship_id = graphene.UUID()
    amount = graphene.Float()
    status = graphene.String()
    due_date = graphene.String()


class FriendLedgerType(graphene.ObjectType):
    friendship_id = graphene.UUID()
    net_balance = graphene.Float()
    transactions = graphene.List(LedgerEntryType)


class DashboardSummaryType(graphene.ObjectType):
    user_id = graphene.UUID()
    total_lent = graphene.Float()
    total_borrowed = graphene.Float()
    total_confirmed = graphene.Int()


def _requester_id(info):
    if hasattr(info.context, 'user') and getattr(info.context.user, 'is_authenticated', False):
        return str(info.context.user.id)
    return str(info.context.headers.get('x-user-id', ''))


def resolve_friend_ledger(_root, info, friendship_id):
    requester_id = _requester_id(info)
    if not requester_id:
        raise Exception('Unauthorized')

    sample = (
        Transaction.objects.filter(friendship_id=friendship_id, is_deleted=False)
        .select_related()
        .prefetch_related()
        .first()
    )
    if sample is None:
        return FriendLedgerType(friendship_id=friendship_id, net_balance=0.0, transactions=[])

    if requester_id not in {str(sample.lender_id), str(sample.borrower_id)}:
        raise Exception('Forbidden')

    txs = list(
        Transaction.objects.filter(friendship_id=friendship_id, is_deleted=False)
        .select_related()
        .prefetch_related()
        .order_by('-created_at')
    )
    bal = Balance.objects.filter(friendship_id=friendship_id).first()

    return FriendLedgerType(
        friendship_id=friendship_id,
        net_balance=float(bal.net_balance) if bal else 0.0,
        transactions=[
            LedgerEntryType(
                id=t.id,
                lender_id=t.lender_id,
                borrower_id=t.borrower_id,
                friendship_id=t.friendship_id,
                amount=float(t.amount),
                status=t.status,
                due_date=str(t.due_date),
            )
            for t in txs
        ],
    )


def resolve_dashboard_summary(_root, info, user_id):
    requester_id = _requester_id(info)
    if str(user_id) != requester_id:
        raise Exception('Forbidden')

    qs = Transaction.objects.filter(is_deleted=False).filter(Q(lender_id=user_id) | Q(borrower_id=user_id))
    total_lent = qs.filter(lender_id=user_id, status=Transaction.STATUS_CONFIRMED).aggregate(v=Sum('amount'))['v'] or Decimal('0')
    total_borrowed = qs.filter(borrower_id=user_id, status=Transaction.STATUS_CONFIRMED).aggregate(v=Sum('amount'))['v'] or Decimal('0')
    total_confirmed = qs.filter(status=Transaction.STATUS_CONFIRMED).count()

    return DashboardSummaryType(
        user_id=user_id,
        total_lent=float(total_lent),
        total_borrowed=float(total_borrowed),
        total_confirmed=total_confirmed,
    )

from decimal import Decimal

import graphene

from apps.transactions.analytics import compute_dashboard_summary
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
    pending_receivable = graphene.Float()
    pending_payable = graphene.Float()
    transactions = graphene.List(LedgerEntryType)


class DashboardSummaryType(graphene.ObjectType):
    user_id = graphene.UUID()
    total_lent = graphene.Float()
    total_borrowed = graphene.Float()
    total_confirmed = graphene.Int()
    loyalty_score = graphene.Float()
    monthly_trend = graphene.List(lambda: MonthlyTrendType)


class MonthlyTrendType(graphene.ObjectType):
    month_key = graphene.String()
    label = graphene.String()
    given = graphene.Float()
    received = graphene.Float()


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
    pending_receivable = Decimal('0')
    pending_payable = Decimal('0')
    for tx in txs:
        if tx.status != Transaction.STATUS_PENDING:
            continue
        if str(tx.lender_id) == requester_id:
            pending_receivable += Decimal(tx.amount)
        elif str(tx.borrower_id) == requester_id:
            pending_payable += Decimal(tx.amount)

    return FriendLedgerType(
        friendship_id=friendship_id,
        net_balance=float(bal.net_balance) if bal else 0.0,
        pending_receivable=float(pending_receivable),
        pending_payable=float(pending_payable),
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

    try:
        computed = compute_dashboard_summary(str(user_id))
    except Exception:
        computed = type(
            'SummaryFallback',
            (),
            {
                'total_lent': 0.0,
                'total_borrowed': 0.0,
                'total_confirmed': 0,
                'loyalty_score': 0.0,
                'monthly_trend': [],
            },
        )()

    return DashboardSummaryType(
        user_id=user_id,
        total_lent=computed.total_lent,
        total_borrowed=computed.total_borrowed,
        total_confirmed=computed.total_confirmed,
        loyalty_score=computed.loyalty_score,
        monthly_trend=[
            MonthlyTrendType(
                month_key=row.month_key,
                label=row.label,
                given=row.given,
                received=row.received,
            )
            for row in computed.monthly_trend
        ],
    )

from decimal import Decimal

import graphene

from apps.transactions.analytics import compute_dashboard_summary
from apps.balances.models import Balance
from apps.transactions.models import DueRecord, Repayment, Transaction, UserDirectory


class LedgerEntryType(graphene.ObjectType):
    id = graphene.UUID()
    lender_id = graphene.UUID()
    borrower_id = graphene.UUID()
    friendship_id = graphene.UUID()
    amount = graphene.Float()
    status = graphene.String()
    due_date = graphene.String()
    note = graphene.String()
    created_at = graphene.String()


class FriendLedgerType(graphene.ObjectType):
    friendship_id = graphene.UUID()
    net_balance = graphene.Float()
    pending_receivable = graphene.Float()
    pending_payable = graphene.Float()
    active_due_total = graphene.Float()
    counterpart_owes_you = graphene.String()
    transactions = graphene.List(LedgerEntryType)
    pending_verifications = graphene.List(LedgerEntryType)


def _username(user_id: str) -> str:
    row = UserDirectory.objects.filter(id=user_id).first()
    return row.username if row is not None else 'Your friend'


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

    txs = list(
        Transaction.objects.filter(friendship_id=friendship_id, is_deleted=False)
        .order_by('-created_at')
    )
    repayments = list(
        Repayment.objects.filter(friendship_id=friendship_id).order_by('-created_at')
    )
    if not txs and not repayments:
        return FriendLedgerType(friendship_id=friendship_id, net_balance=0.0, transactions=[], pending_verifications=[])

    sample = txs[0] if txs else None
    repayment_sample = repayments[0] if repayments else None
    if sample is not None and requester_id not in {str(sample.lender_id), str(sample.borrower_id)}:
        raise Exception('Forbidden')
    if sample is None and repayment_sample is not None and requester_id not in {str(repayment_sample.payee_id), str(repayment_sample.payer_id)}:
        raise Exception('Forbidden')

    bal = Balance.objects.filter(friendship_id=friendship_id).first()
    pending_receivable = Decimal('0')
    pending_payable = Decimal('0')
    active_due_total = Decimal('0')
    pending_verifications: list[LedgerEntryType] = []
    for tx in txs:
        if tx.status == Transaction.STATUS_PENDING_VERIFICATION:
            if str(tx.lender_id) == requester_id:
                pending_receivable += Decimal(tx.amount)
            elif str(tx.borrower_id) == requester_id:
                pending_payable += Decimal(tx.amount)
                pending_verifications.append(
                    LedgerEntryType(
                        id=tx.id,
                        lender_id=tx.lender_id,
                        borrower_id=tx.borrower_id,
                        friendship_id=tx.friendship_id,
                        amount=float(tx.amount),
                        status=tx.status,
                        due_date=str(tx.due_date) if tx.due_date else '',
                        note=tx.note or '',
                        created_at=tx.created_at.isoformat(),
                    )
                )

    due_rows = DueRecord.objects.filter(friendship_id=friendship_id, status=DueRecord.STATUS_ACTIVE)
    for row in due_rows:
        if str(row.lender_id) == requester_id:
            active_due_total += Decimal(row.remaining_amount)
        elif str(row.borrower_id) == requester_id:
            active_due_total -= Decimal(row.remaining_amount)

    tx_entries = [
        LedgerEntryType(
            id=t.id,
            lender_id=t.lender_id,
            borrower_id=t.borrower_id,
            friendship_id=t.friendship_id,
            amount=float(t.amount),
            status=t.status,
            due_date=str(t.due_date) if t.due_date else '',
            note=t.note or '',
            created_at=t.created_at.isoformat(),
        )
        for t in txs
    ]
    repayment_entries = [
        LedgerEntryType(
            id=r.id,
            lender_id=r.payee_id,
            borrower_id=r.payer_id,
            friendship_id=r.friendship_id,
            amount=float(r.amount),
            status='repayment',
            due_date='',
            note=r.note or '',
            created_at=r.created_at.isoformat(),
        )
        for r in repayments
    ]
    merged_entries = sorted(
        [*tx_entries, *repayment_entries],
        key=lambda row: row.created_at or '',
        reverse=True,
    )

    counterpart_name = ''
    if sample is not None:
        counterpart_id = str(sample.borrower_id) if str(sample.lender_id) == requester_id else str(sample.lender_id)
        counterpart_name = _username(counterpart_id)
    elif repayment_sample is not None:
        counterpart_id = str(repayment_sample.payer_id) if str(repayment_sample.payee_id) == requester_id else str(repayment_sample.payee_id)
        counterpart_name = _username(counterpart_id)

    return FriendLedgerType(
        friendship_id=friendship_id,
        net_balance=float(bal.net_balance) if bal else 0.0,
        pending_receivable=float(pending_receivable),
        pending_payable=float(pending_payable),
        active_due_total=float(abs(active_due_total)),
        counterpart_owes_you=f'{counterpart_name} owes you {abs(active_due_total):.2f} Taka' if active_due_total > 0 else '',
        transactions=merged_entries,
        pending_verifications=pending_verifications,
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

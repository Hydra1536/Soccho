import json
from datetime import timedelta
from decimal import Decimal

import redis
from django.conf import settings
from django.db import transaction as db_transaction
from django.http import HttpRequest
from django.utils import timezone
from ninja import NinjaAPI, Router

from apps.balances.services import update_balance_latest
from apps.transactions.analytics import compute_dashboard_summary
from apps.transactions.models import Repayment, Transaction, UserDirectory
from apps.transactions.schemas import RepaymentCreateIn, ResolveTransactionIn, TransactionCreateIn, TransactionOut
from apps.transactions.services import (
    apply_repayment_fifo,
    compute_balance_delta,
    ensure_pending_verification,
    get_transaction_for_update,
    mark_agreed,
    mark_rejected,
)

router = Router(tags=['transactions'])


def _redis_client():
    return redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)


def _publish(event_name: str, payload: dict):
    client = _redis_client()
    client.publish(event_name, json.dumps(payload))


def _requester_id(request: HttpRequest) -> str:
    return str(request.headers.get('x-user-id', '')).strip()


def _requester_username(request: HttpRequest) -> str:
    return str(request.headers.get('x-username', '')).strip()


def _user_name(user_id: str) -> str:
    row = UserDirectory.objects.filter(id=user_id).first()
    return row.username if row is not None else 'A friend'


def _format_money(amount: Decimal | str) -> str:
    return f"{Decimal(amount):.2f}"


def _due_date_text(value) -> str:
    return str(value) if value else 'No due date'


def _hard_evict_related_caches(friendship_id: str, user_ids: list[str]) -> None:
    client = _redis_client()
    keys: list[str] = []
    for user_id in user_ids:
        keys.extend(
            [
                f'loyalty_score:{user_id}',
                f'friend_list:{user_id}',
                f'friend_requests:{user_id}',
                f'profile_snapshot:{user_id}',
            ]
        )
    keys.append(f'friend_ledger:{friendship_id}')
    if keys:
        client.delete(*keys)
    client.publish(
        'cache.invalidate',
        json.dumps(
            {
                'friendship_id': friendship_id,
                'user_ids': user_ids,
                'strategy': 'hard-evict-and-rebuild',
                'occurred_at': timezone.now().isoformat(),
            }
        ),
    )


def _serialize_transaction(tx: Transaction) -> dict:
    return {
        'id': str(tx.id),
        'lender_id': str(tx.lender_id),
        'borrower_id': str(tx.borrower_id),
        'friendship_id': str(tx.friendship_id),
        'friendship_route_id': tx.friendship_route_id or '',
        'amount': str(tx.amount),
        'due_date': str(tx.due_date) if tx.due_date else None,
        'note': tx.note or '',
        'status': tx.status,
        'idempotency_key': tx.idempotency_key,
        'created_at': tx.created_at.isoformat(),
        'updated_at': tx.updated_at.isoformat(),
        'lender_name': _user_name(str(tx.lender_id)),
        'borrower_name': _user_name(str(tx.borrower_id)),
    }


@router.post('/', response={201: TransactionOut, 200: TransactionOut, 403: dict, 409: dict})
def create_transaction(request: HttpRequest, payload: TransactionCreateIn):
    requester_id = _requester_id(request)
    if requester_id and requester_id != str(payload.lender_id):
        return 403, {'detail': 'Only the lender can create a transaction log'}

    client = _redis_client()
    lock_key = f'idempotency:transaction:create:{payload.idempotency_key}'
    acquired = client.set(lock_key, '1', nx=True, ex=int(timedelta(hours=24).total_seconds()))
    if not acquired:
        existing = Transaction.objects.filter(idempotency_key=payload.idempotency_key).first()
        if existing is None:
            return 409, {'detail': 'Duplicate idempotency key'}
        return 200, existing

    with db_transaction.atomic():
        tx = Transaction.objects.create(
            lender_id=payload.lender_id,
            borrower_id=payload.borrower_id,
            friendship_id=payload.friendship_id,
            friendship_route_id=payload.friendship_route_id or '',
            amount=payload.amount,
            due_date=payload.due_date,
            note=payload.note or '',
            idempotency_key=payload.idempotency_key,
            status=Transaction.STATUS_PENDING_VERIFICATION,
        )

    lender_name = _requester_username(request) or _user_name(str(tx.lender_id))
    _publish(
        'transaction.verification_requested',
        {
            'transaction_id': str(tx.id),
            'friendship_id': str(tx.friendship_id),
            'recipient_id': str(tx.borrower_id),
            'lender_id': str(tx.lender_id),
            'borrower_id': str(tx.borrower_id),
            'lender_name': lender_name,
            'amount': _format_money(tx.amount),
            'note': tx.note or '',
            'due_date': str(tx.due_date) if tx.due_date else '',
            'title': 'Transaction verification needed',
            'body': f'{lender_name} sent you a {_format_money(tx.amount)} Taka log. Please verify.',
            'route': f'/friend/{tx.friendship_route_id or tx.friendship_id}?tab=verifications',
        },
    )
    return 201, tx


@router.get('/pending-verifications/', response={200: dict, 401: dict})
def list_pending_verifications(request: HttpRequest, friendship_id: str | None = None):
    requester_id = _requester_id(request)
    if not requester_id:
        return 401, {'detail': 'Invalid credentials'}

    queryset = Transaction.objects.filter(
        borrower_id=requester_id,
        status=Transaction.STATUS_PENDING_VERIFICATION,
        is_deleted=False,
    ).order_by('-created_at')
    if friendship_id:
        queryset = queryset.filter(friendship_id=friendship_id)

    return 200, {'results': [_serialize_transaction(row) for row in queryset]}


@router.post('/{transaction_id}/resolve/', response={200: TransactionOut, 403: dict, 404: dict, 409: dict})
def resolve_transaction(request: HttpRequest, transaction_id: str, payload: ResolveTransactionIn):
    action = payload.action.strip().lower()
    if action not in {'agree', 'disagree'}:
        return 409, {'detail': 'Unsupported action'}

    requester_id = _requester_id(request)
    if requester_id and requester_id != str(payload.borrower_id):
        return 403, {'detail': 'Only the borrower can resolve the transaction'}

    with db_transaction.atomic():
        tx = get_transaction_for_update(transaction_id)
        if tx is None:
            return 404, {'detail': 'Transaction not found'}

        if str(tx.borrower_id) != str(payload.borrower_id):
            return 403, {'detail': 'Only borrower can resolve'}

        try:
            ensure_pending_verification(tx)
        except ValueError:
            return 409, {'detail': 'Transaction is not pending verification'}

        if action == 'agree':
            delta = compute_balance_delta(tx)
            balance = update_balance_latest(tx.friendship_id, delta)
            tx, _due_record = mark_agreed(tx)
            borrower_name = _requester_username(request) or _user_name(str(tx.borrower_id))
            _publish(
                'transaction.verified',
                {
                    'transaction_id': str(tx.id),
                    'friendship_id': str(tx.friendship_id),
                    'recipient_id': str(tx.lender_id),
                    'new_version': balance.version,
                    'net_balance': str(balance.net_balance),
                    'borrower_id': str(tx.borrower_id),
                    'borrower_name': borrower_name,
                    'lender_id': str(tx.lender_id),
                    'amount': _format_money(tx.amount),
                    'note': tx.note or '',
                    'due_date': str(tx.due_date) if tx.due_date else '',
                    'title': 'Transaction agreed',
                    'body': f'{borrower_name} has agreed to receive your log of {_format_money(tx.amount)} Taka. Note: {tx.note or "None"}, Due Date: {_due_date_text(tx.due_date)}',
                    'route': f'/friend/{tx.friendship_route_id or tx.friendship_id}',
                },
            )
            _hard_evict_related_caches(str(tx.friendship_id), [str(tx.borrower_id), str(tx.lender_id)])
            return 200, tx

        tx = mark_rejected(tx)
        borrower_name = _requester_username(request) or _user_name(str(tx.borrower_id))
        _publish(
            'transaction.rejected',
            {
                'transaction_id': str(tx.id),
                'friendship_id': str(tx.friendship_id),
                'recipient_id': str(tx.lender_id),
                'borrower_id': str(tx.borrower_id),
                'borrower_name': borrower_name,
                'lender_id': str(tx.lender_id),
                'amount': _format_money(tx.amount),
                'title': 'Transaction disagreed',
                'body': f'{borrower_name} disagreed with your transaction log.',
                'route': f'/friend/{tx.friendship_route_id or tx.friendship_id}',
            },
        )
        return 200, tx


@router.post('/repayments/', response={201: dict, 200: dict, 403: dict, 409: dict})
def create_repayment(request: HttpRequest, payload: RepaymentCreateIn):
    requester_id = _requester_id(request)
    if requester_id and requester_id != str(payload.payer_id):
        return 403, {'detail': 'Only the payer can record a repayment'}

    client = _redis_client()
    lock_key = f'idempotency:repayment:create:{payload.idempotency_key}'
    acquired = client.set(lock_key, '1', nx=True, ex=int(timedelta(hours=24).total_seconds()))
    if not acquired:
        existing = Repayment.objects.filter(idempotency_key=payload.idempotency_key).first()
        if existing is not None:
            return 200, {'repayment_id': str(existing.id), 'detail': 'Repayment already recorded'}
        return 409, {'detail': 'Duplicate idempotency key'}

    try:
        amount = Decimal(payload.amount)
    except Exception:
        return 409, {'detail': 'Invalid repayment amount'}

    with db_transaction.atomic():
        try:
            allocation = apply_repayment_fifo(payload.friendship_id, payload.payer_id, payload.payee_id, amount)
        except ValueError as exc:
            return 409, {'detail': str(exc)}

        repayment = Repayment.objects.create(
            friendship_id=payload.friendship_id,
            payer_id=payload.payer_id,
            payee_id=payload.payee_id,
            amount=amount,
            idempotency_key=payload.idempotency_key,
            note=payload.note or '',
        )
        balance = update_balance_latest(payload.friendship_id, Decimal('0') - amount)

    payer_name = _requester_username(request) or _user_name(str(payload.payer_id))
    _publish(
        'transaction.repayment_recorded',
        {
            'repayment_id': str(repayment.id),
            'friendship_id': str(payload.friendship_id),
            'recipient_id': str(payload.payee_id),
            'payer_id': str(payload.payer_id),
            'payer_name': payer_name,
            'amount': _format_money(amount),
            'note': payload.note or '',
            'allocations': allocation['allocations'],
            'title': 'Repayment recorded',
            'body': f'{payer_name} recorded a repayment of {_format_money(amount)} Taka.',
            'route': f'/friend/{payload.friendship_route_id or payload.friendship_id}',
            'new_version': balance.version,
            'net_balance': str(balance.net_balance),
        },
    )
    _hard_evict_related_caches(str(payload.friendship_id), [str(payload.payer_id), str(payload.payee_id)])
    return 201, {'repayment_id': str(repayment.id), 'allocation': allocation}


@router.get('/loyalty-score/', response={200: dict, 401: dict})
def loyalty_score(request: HttpRequest):
    user_id = _requester_id(request)
    if not user_id:
        return 401, {'detail': 'Invalid credentials'}

    try:
        computed = compute_dashboard_summary(user_id)
    except Exception:
        computed = type('ScoreFallback', (), {'loyalty_score': 0.0, 'total_lent': 0.0, 'total_borrowed': 0.0})()
    return 200, {
        'user_id': user_id,
        'loyalty_score': computed.loyalty_score,
        'total_lent': computed.total_lent,
        'total_borrowed': computed.total_borrowed,
    }


api = NinjaAPI(title='Soccho Transaction Service')
api.add_router('', router)

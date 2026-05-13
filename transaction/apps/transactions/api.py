import json
from datetime import timedelta

import redis
from django.conf import settings
from django.db import transaction as db_transaction
from django.http import HttpRequest
from ninja import NinjaAPI, Router

from apps.balances.services import BalanceVersionConflict, update_balance
from apps.transactions.models import Transaction
from apps.transactions.schemas import ConfirmTransactionIn, TransactionCreateIn, TransactionOut
from apps.transactions.services import compute_balance_delta, ensure_pending, get_transaction_for_update, mark_confirmed

router = Router(tags=['transactions'])


def _redis_client():
    return redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)


def _publish(event_name: str, payload: dict):
    client = _redis_client()
    client.publish(event_name, json.dumps(payload))


@router.post('/', response={201: TransactionOut, 200: TransactionOut, 409: dict})
def create_transaction(request: HttpRequest, payload: TransactionCreateIn):
    client = _redis_client()
    lock_key = f"idempotency:transaction:create:{payload.idempotency_key}"

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
            amount=payload.amount,
            due_date=payload.due_date,
            idempotency_key=payload.idempotency_key,
            status=Transaction.STATUS_PENDING,
        )

    _publish('transaction.created', {
        'transaction_id': str(tx.id),
        'friendship_id': str(tx.friendship_id),
        'lender_id': str(tx.lender_id),
        'borrower_id': str(tx.borrower_id),
        'amount': str(tx.amount),
        'due_date': str(tx.due_date),
    })
    return 201, tx


@router.post('/{transaction_id}/confirm/', response={200: TransactionOut, 403: dict, 404: dict, 409: dict})
def confirm_transaction(request: HttpRequest, transaction_id: str, payload: ConfirmTransactionIn):
    with db_transaction.atomic():
        tx = get_transaction_for_update(transaction_id)
        if tx is None:
            return 404, {'detail': 'Transaction not found'}

        if str(tx.borrower_id) != str(payload.borrower_id):
            return 403, {'detail': 'Only borrower can confirm'}

        try:
            ensure_pending(tx)
        except ValueError:
            return 409, {'detail': 'Transaction is not pending'}

        delta = compute_balance_delta(tx)
        try:
            balance = update_balance(tx.friendship_id, delta, payload.expected_version)
        except BalanceVersionConflict:
            return 409, {'detail': 'Version mismatch'}

        tx = mark_confirmed(tx)

    _publish('transaction.confirmed', {
        'transaction_id': str(tx.id),
        'friendship_id': str(tx.friendship_id),
        'new_version': balance.version,
        'net_balance': str(balance.net_balance),
    })
    return 200, tx


api = NinjaAPI(title='Soccho Transaction Service')
api.add_router('', router)

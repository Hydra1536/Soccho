from decimal import Decimal

from django.db import transaction as db_transaction

from apps.transactions.models import Transaction


def get_transaction_for_update(transaction_id):
    return Transaction.objects.select_for_update().filter(id=transaction_id, is_deleted=False).first()


def ensure_pending(transaction_obj: Transaction) -> None:
    if transaction_obj.status != Transaction.STATUS_PENDING:
        raise ValueError('Transaction is not pending')


def compute_balance_delta(transaction_obj: Transaction) -> Decimal:
    # Positive delta means borrower owes lender more.
    return Decimal(transaction_obj.amount)


@db_transaction.atomic
def mark_confirmed(transaction_obj: Transaction) -> Transaction:
    transaction_obj.status = Transaction.STATUS_CONFIRMED
    transaction_obj.save(update_fields=['status', 'updated_at'])
    return transaction_obj

from datetime import date
from decimal import Decimal

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.transactions.models import DueRecord, Transaction


def get_transaction_for_update(transaction_id):
    return (
        Transaction.objects.select_for_update()
        .filter(id=transaction_id, is_deleted=False)
        .first()
    )


def ensure_pending_verification(transaction_obj: Transaction) -> None:
    if transaction_obj.status != Transaction.STATUS_PENDING_VERIFICATION:
        raise ValueError("Transaction is not pending verification")


def compute_balance_delta(transaction_obj: Transaction) -> Decimal:
    # Positive delta means borrower owes lender more.
    return Decimal(transaction_obj.amount)


@db_transaction.atomic
def mark_agreed(transaction_obj: Transaction) -> tuple[Transaction, DueRecord]:
    transaction_obj.status = Transaction.STATUS_AGREED
    transaction_obj.verified_at = timezone.now()
    transaction_obj.rejected_at = None
    transaction_obj.save(
        update_fields=["status", "verified_at", "rejected_at", "updated_at"]
    )
    due_record, _ = DueRecord.objects.update_or_create(
        transaction_id=transaction_obj.id,
        defaults={
            "lender_id": transaction_obj.lender_id,
            "borrower_id": transaction_obj.borrower_id,
            "friendship_id": transaction_obj.friendship_id,
            "friendship_route_id": transaction_obj.friendship_route_id or "",
            "original_amount": Decimal(transaction_obj.amount),
            "remaining_amount": Decimal(transaction_obj.amount),
            "due_date": transaction_obj.due_date,
            "status": DueRecord.STATUS_ACTIVE,
            "settled_at": None,
        },
    )
    return transaction_obj, due_record


@db_transaction.atomic
def mark_rejected(transaction_obj: Transaction) -> Transaction:
    transaction_obj.status = Transaction.STATUS_REJECTED
    transaction_obj.rejected_at = timezone.now()
    transaction_obj.verified_at = None
    transaction_obj.save(
        update_fields=["status", "rejected_at", "verified_at", "updated_at"]
    )
    return transaction_obj


@db_transaction.atomic
def apply_repayment_fifo(friendship_id, payer_id, payee_id, amount: Decimal):
    if amount <= 0:
        raise ValueError("Repayment amount must be greater than zero")

    rows = list(
        DueRecord.objects.select_for_update().filter(
            friendship_id=friendship_id,
            borrower_id=payer_id,
            lender_id=payee_id,
            status=DueRecord.STATUS_ACTIVE,
        )
    )
    rows.sort(key=lambda row: (row.due_date or date.max, row.created_at))
    outstanding = sum(
        (Decimal(row.remaining_amount) for row in rows), start=Decimal("0")
    )
    if amount > outstanding:
        raise ValueError("Repayment amount exceeds outstanding due")

    remaining = Decimal(amount)
    allocations: list[dict] = []
    settled_transaction_ids: list[str] = []
    now = timezone.now()
    for row in rows:
        if remaining <= 0:
            break
        row_remaining = Decimal(row.remaining_amount)
        if row_remaining <= 0:
            continue
        applied = row_remaining if row_remaining <= remaining else remaining
        next_remaining = row_remaining - applied
        row.remaining_amount = next_remaining
        if next_remaining == 0:
            row.status = DueRecord.STATUS_SETTLED
            row.settled_at = now
            settled_transaction_ids.append(str(row.transaction_id))
            Transaction.objects.filter(id=row.transaction_id).update(
                status=Transaction.STATUS_SETTLED,
                updated_at=now,
            )
        row.save(
            update_fields=["remaining_amount", "status", "settled_at", "updated_at"]
        )
        allocations.append(
            {
                "due_record_id": str(row.id),
                "transaction_id": str(row.transaction_id),
                "applied_amount": str(applied),
                "remaining_amount": str(next_remaining),
                "due_date": str(row.due_date) if row.due_date else "",
            }
        )
        remaining -= applied

    return {
        "applied_total": str(amount - remaining),
        "remaining_input_amount": str(remaining),
        "allocations": allocations,
        "settled_transaction_ids": settled_transaction_ids,
    }

import uuid
from datetime import date
from decimal import Decimal

from ninja import Schema


class TransactionCreateIn(Schema):
    lender_id: uuid.UUID
    borrower_id: uuid.UUID
    friendship_id: uuid.UUID
    friendship_route_id: str = ''
    amount: Decimal
    due_date: date | None = None
    note: str = ''
    idempotency_key: str


class TransactionOut(Schema):
    id: uuid.UUID
    lender_id: uuid.UUID
    borrower_id: uuid.UUID
    friendship_id: uuid.UUID
    friendship_route_id: str
    amount: Decimal
    due_date: date | None = None
    note: str
    status: str
    idempotency_key: str


class ConfirmTransactionIn(Schema):
    borrower_id: uuid.UUID
    expected_version: int


class ResolveTransactionIn(Schema):
    borrower_id: uuid.UUID
    action: str


class RepaymentCreateIn(Schema):
    friendship_id: uuid.UUID
    friendship_route_id: str = ''
    payer_id: uuid.UUID
    payee_id: uuid.UUID
    amount: Decimal
    note: str = ''
    idempotency_key: str

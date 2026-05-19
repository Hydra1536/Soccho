from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q

from apps.transactions.models import Transaction


@dataclass
class MonthlySummaryRow:
    month_key: str
    label: str
    given: float
    received: float


@dataclass
class DashboardSummaryComputed:
    total_lent: float
    total_borrowed: float
    total_confirmed: int
    loyalty_score: float
    monthly_trend: list[MonthlySummaryRow]


def _month_iter(start_year: int, start_month: int, end_year: int, end_month: int):
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        yield year, month
        month += 1
        if month > 12:
            month = 1
            year += 1


def compute_loyalty_score(user_id: str, rows: list[Transaction]) -> float:
    if not rows:
        return 0.0

    confirmed_rows = [row for row in rows if row.status == Transaction.STATUS_CONFIRMED]
    total_lent = sum((Decimal(row.amount) for row in confirmed_rows if str(row.lender_id) == user_id), start=Decimal('0'))
    total_borrowed = sum((Decimal(row.amount) for row in confirmed_rows if str(row.borrower_id) == user_id), start=Decimal('0'))

    unique_confirmed_counterparts = {
        str(row.borrower_id) if str(row.lender_id) == user_id else str(row.lender_id)
        for row in confirmed_rows
        if str(row.lender_id) == user_id or str(row.borrower_id) == user_id
    }

    borrow_rows = [row for row in rows if str(row.borrower_id) == user_id]
    confirmed_borrow_rows = [row for row in borrow_rows if row.status == Transaction.STATUS_CONFIRMED]
    due_borrow_rows = [row for row in confirmed_borrow_rows if row.due_date is not None]

    if due_borrow_rows:
        on_time_hits = sum(
            1
            for row in due_borrow_rows
            if row.updated_at is not None and row.updated_at.date() <= row.due_date
        )
        on_time_rate = on_time_hits / len(due_borrow_rows)
    else:
        on_time_rate = 1.0

    if borrow_rows:
        completion_rate = len(confirmed_borrow_rows) / len(borrow_rows)
    else:
        completion_rate = 1.0

    total_flow = total_lent + total_borrowed
    if total_flow > 0:
        lend_advantage = (total_lent - total_borrowed) / total_flow
        lend_component = float((lend_advantage + Decimal('1')) / Decimal('2'))
    else:
        lend_component = 0.5

    network_diversity = min(1.0, len(unique_confirmed_counterparts) / 10.0)
    today = date.today()
    overdue_pending = [
        row
        for row in borrow_rows
        if row.status == Transaction.STATUS_PENDING and row.due_date is not None and row.due_date < today
    ]
    overdue_penalty = (len(overdue_pending) / len(borrow_rows)) if borrow_rows else 0.0
    activity = min(1.0, len(confirmed_rows) / 20.0)

    score = 100.0 * (
        0.40 * on_time_rate
        + 0.25 * lend_component
        + 0.20 * completion_rate
        + 0.10 * network_diversity
        + 0.05 * activity
    )
    score -= 20.0 * overdue_penalty
    return max(0.0, min(100.0, score))


def compute_dashboard_summary(user_id: str) -> DashboardSummaryComputed:
    rows = list(
        Transaction.objects.filter(is_deleted=False)
        .filter(Q(lender_id=user_id) | Q(borrower_id=user_id))
        .only('lender_id', 'borrower_id', 'amount', 'status', 'created_at', 'due_date', 'updated_at')
        .order_by('created_at')
    )

    effective_rows = [row for row in rows if row.status != Transaction.STATUS_DENIED]
    confirmed_rows = [row for row in effective_rows if row.status == Transaction.STATUS_CONFIRMED]
    total_lent = sum((Decimal(row.amount) for row in effective_rows if str(row.lender_id) == user_id), start=Decimal('0'))
    total_borrowed = sum((Decimal(row.amount) for row in effective_rows if str(row.borrower_id) == user_id), start=Decimal('0'))
    total_confirmed = len(confirmed_rows)

    monthly_map: dict[str, dict[str, Decimal | str]] = {}
    for row in effective_rows:
        month_key = row.created_at.strftime('%Y-%m')
        if month_key not in monthly_map:
            monthly_map[month_key] = {
                'month_key': month_key,
                'label': row.created_at.strftime('%b %y'),
                'given': Decimal('0'),
                'received': Decimal('0'),
            }
        amount = Decimal(row.amount)
        if str(row.lender_id) == user_id:
            monthly_map[month_key]['given'] = Decimal(monthly_map[month_key]['given']) + amount
        if str(row.borrower_id) == user_id:
            monthly_map[month_key]['received'] = Decimal(monthly_map[month_key]['received']) + amount

    monthly_trend: list[MonthlySummaryRow] = []
    today = date.today()
    end_year = today.year
    end_month = today.month
    start_year = end_year
    start_month = end_month - 11
    if start_month <= 0:
        start_year -= 1
        start_month += 12

    for year, month in _month_iter(start_year, start_month, end_year, end_month):
        key = f'{year:04d}-{month:02d}'
        if key in monthly_map:
            row = monthly_map[key]
            monthly_trend.append(
                MonthlySummaryRow(
                    month_key=str(row['month_key']),
                    label=str(row['label']),
                    given=float(Decimal(row['given'])),
                    received=float(Decimal(row['received'])),
                )
            )
        else:
            monthly_trend.append(
                MonthlySummaryRow(
                    month_key=key,
                    label=date(year, month, 1).strftime('%b %y'),
                    given=0.0,
                    received=0.0,
                )
            )

    loyalty_score = compute_loyalty_score(user_id, rows)

    return DashboardSummaryComputed(
        total_lent=float(total_lent),
        total_borrowed=float(total_borrowed),
        total_confirmed=total_confirmed,
        loyalty_score=loyalty_score,
        monthly_trend=monthly_trend,
    )

from decimal import Decimal

from django.db import transaction as db_transaction

from apps.balances.models import Balance


class BalanceVersionConflict(Exception):
    pass


@db_transaction.atomic
def update_balance(friendship_id, delta: Decimal, expected_version: int) -> Balance:
    balance = Balance.objects.select_for_update().filter(friendship_id=friendship_id).first()
    if balance is None:
        if expected_version != 0:
            raise BalanceVersionConflict('Version mismatch')
        balance = Balance.objects.create(friendship_id=friendship_id, net_balance=Decimal('0'), version=0)

    if balance.version != expected_version:
        raise BalanceVersionConflict('Version mismatch')

    balance.net_balance = Decimal(balance.net_balance) + Decimal(delta)
    balance.version += 1
    balance.save(update_fields=['net_balance', 'version', 'updated_at'])
    return balance


@db_transaction.atomic
def update_balance_latest(friendship_id, delta: Decimal) -> Balance:
    balance = Balance.objects.select_for_update().filter(friendship_id=friendship_id).first()
    if balance is None:
        balance = Balance.objects.create(friendship_id=friendship_id, net_balance=Decimal('0'), version=0)

    balance.net_balance = Decimal(balance.net_balance) + Decimal(delta)
    balance.version += 1
    balance.save(update_fields=['net_balance', 'version', 'updated_at'])
    return balance

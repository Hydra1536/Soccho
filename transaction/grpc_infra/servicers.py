from django.db.models import Sum

from apps.balances.models import Balance
from apps.transactions.models import Transaction
from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc


class TransactionServicer(soccho_pb2_grpc.TransactionServiceServicer):
    def GetBalance(self, request, context):
        friendship_id = request.friendship_id
        user_id = str(getattr(request, 'user_id', '') or '')

        balance = Balance.objects.filter(friendship_id=friendship_id).first()
        net = float(balance.net_balance) if balance is not None else 0.0

        confirmed = Transaction.objects.filter(
            friendship_id=friendship_id,
            status=Transaction.STATUS_CONFIRMED,
            is_deleted=False,
        )

        if user_id:
            total_given = float((confirmed.filter(lender_id=user_id).aggregate(v=Sum('amount'))['v'] or 0.0))
            total_lent = float((confirmed.filter(borrower_id=user_id).aggregate(v=Sum('amount'))['v'] or 0.0))
        else:
            aggregate_total = float((confirmed.aggregate(v=Sum('amount'))['v'] or 0.0))
            total_given = aggregate_total
            total_lent = aggregate_total

        total_transactions = confirmed.count()

        return soccho_pb2.GetBalanceResponse(
            friendship_id=str(friendship_id),
            net_balance=net,
            total_given=total_given,
            total_lent=total_lent,
            total_transactions=int(total_transactions),
        )

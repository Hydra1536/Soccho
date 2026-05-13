from uuid import UUID

import grpc

from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc


_auth_channel = grpc.aio.insecure_channel('auth:8001')
_auth_stub = soccho_pb2_grpc.AuthServiceStub(_auth_channel)

_transaction_channel = grpc.aio.insecure_channel('transaction:8003')
_transaction_stub = soccho_pb2_grpc.TransactionServiceStub(_transaction_channel)


class AuthClientAdapter:
    async def GetUserInfo(self, user_id: str):
        return await _auth_stub.GetUserInfo(soccho_pb2.GetUserInfoRequest(user_id=str(user_id)))


class TransactionClientAdapter:
    async def GetBalanceForLoyalty(self, user_id: str):
        return await _transaction_stub.GetBalance(soccho_pb2.GetBalanceRequest(user_id=str(user_id)))


def get_auth_client() -> AuthClientAdapter:
    return AuthClientAdapter()


def get_transaction_client() -> TransactionClientAdapter:
    return TransactionClientAdapter()

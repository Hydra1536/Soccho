import os

import grpc

from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc

AUTH_GRPC_HOST = os.getenv('AUTH_GRPC_HOST', 'auth')
AUTH_GRPC_PORT = os.getenv('AUTH_GRPC_PORT', '8001')
TRANSACTION_GRPC_HOST = os.getenv('TRANSACTION_GRPC_HOST', 'transaction')
TRANSACTION_GRPC_PORT = os.getenv('TRANSACTION_GRPC_PORT', '8003')

_auth_channel = grpc.aio.insecure_channel(f'{AUTH_GRPC_HOST}:{AUTH_GRPC_PORT}')
_auth_stub = soccho_pb2_grpc.AuthServiceStub(_auth_channel)

_transaction_channel = grpc.aio.insecure_channel(f'{TRANSACTION_GRPC_HOST}:{TRANSACTION_GRPC_PORT}')
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

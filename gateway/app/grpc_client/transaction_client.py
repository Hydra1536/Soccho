from typing import Optional

import grpc

from app.config import get_settings
from app.grpc_client.generated import soccho_pb2, soccho_pb2_grpc


class TransactionClient:
    def __init__(self) -> None:
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[soccho_pb2_grpc.TransactionServiceStub] = None

    async def connect(self) -> None:
        settings = get_settings()
        target = f"{settings.transaction_grpc_host}:{settings.transaction_grpc_port}"
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = soccho_pb2_grpc.TransactionServiceStub(self.channel)

    async def close(self) -> None:
        if self.channel is not None:
            await self.channel.close()

    async def get_balance(self, user_id: str):
        if self.stub is None:
            raise RuntimeError('Transaction gRPC client is not initialized')
        request = soccho_pb2.GetBalanceRequest(user_id=user_id)
        return await self.stub.GetBalance(request)


transaction_client = TransactionClient()

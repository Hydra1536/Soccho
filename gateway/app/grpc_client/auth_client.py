from typing import Optional

import grpc

from app.config import get_settings
from app.grpc_client.generated import soccho_pb2, soccho_pb2_grpc


class AuthClient:
    def __init__(self) -> None:
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[soccho_pb2_grpc.AuthServiceStub] = None

    async def connect(self) -> None:
        settings = get_settings()
        target = f"{settings.auth_grpc_host}:{settings.auth_grpc_port}"
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = soccho_pb2_grpc.AuthServiceStub(self.channel)

    async def close(self) -> None:
        if self.channel is not None:
            await self.channel.close()

    async def validate_token(self, token: str):
        if self.stub is None:
            raise RuntimeError('Auth gRPC client is not initialized')
        request = soccho_pb2.ValidateTokenRequest(token=token)
        return await self.stub.ValidateToken(request)

    async def get_user_info(self, user_id: str):
        if self.stub is None:
            raise RuntimeError('Auth gRPC client is not initialized')
        request = soccho_pb2.GetUserInfoRequest(user_id=user_id)
        return await self.stub.GetUserInfo(request)


auth_client = AuthClient()

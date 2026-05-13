from typing import Optional

import grpc

from app.config import get_settings
from app.grpc_client.generated import soccho_pb2, soccho_pb2_grpc


class SocialClient:
    def __init__(self) -> None:
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[soccho_pb2_grpc.SocialServiceStub] = None

    async def connect(self) -> None:
        settings = get_settings()
        target = f"{settings.social_grpc_host}:{settings.social_grpc_port}"
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = soccho_pb2_grpc.SocialServiceStub(self.channel)

    async def close(self) -> None:
        if self.channel is not None:
            await self.channel.close()

    async def check_friendship(self, user_id: str, friend_id: str):
        if self.stub is None:
            raise RuntimeError('Social gRPC client is not initialized')
        request = soccho_pb2.CheckFriendshipRequest(user_id=user_id, friend_id=friend_id)
        return await self.stub.CheckFriendship(request)

    async def get_friend_list(self, user_id: str):
        if self.stub is None:
            raise RuntimeError('Social gRPC client is not initialized')
        request = soccho_pb2.GetFriendListRequest(user_id=user_id)
        return await self.stub.GetFriendList(request)


social_client = SocialClient()

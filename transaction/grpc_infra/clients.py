import os

import grpc
import pybreaker

from grpc_infra.generated import soccho_pb2, soccho_pb2_grpc


class SocialServiceUnavailable(Exception):
    pass


class SocialClient:
    def __init__(self) -> None:
        host = os.getenv('SOCIAL_GRPC_HOST', 'social')
        port = os.getenv('SOCIAL_GRPC_PORT', '8002')
        self.channel = grpc.aio.insecure_channel(f'{host}:{port}')
        self.stub = soccho_pb2_grpc.SocialServiceStub(self.channel)
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)

    async def check_friendship(self, user_id: str, friend_id: str) -> bool:
        req = soccho_pb2.CheckFriendshipRequest(user_id=str(user_id), friend_id=str(friend_id))
        try:
            res = await self.breaker.call_async(self.stub.CheckFriendship, req)
            return bool(getattr(res, 'is_friend', False))
        except Exception as exc:
            raise SocialServiceUnavailable('Service Unavailable') from exc


social_client = SocialClient()

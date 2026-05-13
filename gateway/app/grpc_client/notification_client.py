from typing import Optional

import grpc

from app.config import get_settings
from app.grpc_client.generated import soccho_pb2, soccho_pb2_grpc


class NotificationClient:
    def __init__(self) -> None:
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[soccho_pb2_grpc.NotificationServiceStub] = None

    async def connect(self) -> None:
        settings = get_settings()
        target = f"{settings.notification_grpc_host}:{settings.notification_grpc_port}"
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = soccho_pb2_grpc.NotificationServiceStub(self.channel)

    async def close(self) -> None:
        if self.channel is not None:
            await self.channel.close()

    async def send_notification(self, user_id: str, title: str, body: str, metadata: dict[str, str] | None = None):
        if self.stub is None:
            raise RuntimeError('Notification gRPC client is not initialized')
        request = soccho_pb2.SendNotificationRequest(user_id=user_id, title=title, body=body, metadata=metadata or {})
        return await self.stub.SendNotification(request)


notification_client = NotificationClient()

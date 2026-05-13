from dataclasses import dataclass


@dataclass
class SendNotificationRequest:
    user_id: str = ''
    title: str = ''
    body: str = ''
    metadata: dict[str, str] | None = None


@dataclass
class SendNotificationResponse:
    success: bool = False
    message_id: str = ''
    error: str = ''

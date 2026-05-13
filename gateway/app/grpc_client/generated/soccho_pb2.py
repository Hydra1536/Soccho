from dataclasses import dataclass


@dataclass
class ValidateTokenRequest:
    token: str = ''


@dataclass
class ValidateTokenResponse:
    valid: bool = False
    user_id: str = ''
    error: str = ''


@dataclass
class GetUserInfoRequest:
    user_id: str = ''


@dataclass
class GetUserInfoResponse:
    user_id: str = ''
    username: str = ''
    email: str = ''
    is_active: bool = False


@dataclass
class CheckFriendshipRequest:
    user_id: str = ''
    friend_id: str = ''


@dataclass
class CheckFriendshipResponse:
    is_friend: bool = False


@dataclass
class GetFriendListRequest:
    user_id: str = ''


@dataclass
class Friend:
    user_id: str = ''
    username: str = ''


@dataclass
class GetFriendListResponse:
    friends: list[Friend] | None = None


@dataclass
class GetBalanceRequest:
    user_id: str = ''


@dataclass
class GetBalanceResponse:
    user_id: str = ''
    balance: float = 0.0
    currency: str = ''


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

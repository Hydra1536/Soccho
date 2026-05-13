from dataclasses import dataclass


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
class GetUserInfoRequest:
    user_id: str = ''


@dataclass
class GetUserInfoResponse:
    user_id: str = ''
    username: str = ''
    email: str = ''


@dataclass
class GetBalanceRequest:
    user_id: str = ''


@dataclass
class GetBalanceResponse:
    total_given: float = 0.0
    total_lent: float = 0.0
    total_transactions: int = 0

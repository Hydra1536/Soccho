from dataclasses import dataclass


@dataclass
class CheckFriendshipRequest:
    user_id: str = ''
    friend_id: str = ''


@dataclass
class CheckFriendshipResponse:
    is_friend: bool = False


@dataclass
class GetBalanceRequest:
    friendship_id: str = ''
    user_id: str = ''


@dataclass
class GetBalanceResponse:
    friendship_id: str = ''
    net_balance: float = 0.0
    total_given: float = 0.0
    total_lent: float = 0.0
    total_transactions: int = 0

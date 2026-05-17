from types import SimpleNamespace
from uuid import UUID

import django
from rest_framework.test import APIRequestFactory

django.setup()

from apps.friendships.models import Friendship
from apps.friendships.views import SendRequestView
from apps.friendships import views as friendship_views


def _mock_serializer(_obj):
    return SimpleNamespace(data={"status": _obj.status})


def test_send_request_existing_pending_returns_200(monkeypatch):
    requester_id = UUID("1bc18dc6-e30f-4860-818d-0a5f6fb2b200")
    addressee_id = UUID("b5f8f23d-1d6a-4ac6-b62d-4b8b7d93f971")
    existing = SimpleNamespace(
        requester_id=requester_id,
        addressee_id=addressee_id,
        status=Friendship.STATUS_PENDING,
    )

    monkeypatch.setattr(friendship_views, "_current_user_id", lambda _request: requester_id)
    monkeypatch.setattr(friendship_views, "_find_friendship_pair", lambda *_args, **_kwargs: existing)
    monkeypatch.setattr(friendship_views, "FriendshipSerializer", _mock_serializer)

    request = APIRequestFactory().post(
        "/api/social/send-request/",
        {"user_id": str(addressee_id)},
        format="json",
    )
    response = SendRequestView.as_view()(request)

    assert response.status_code == 200
    assert response.data["detail"] == "Friend request already sent"


def test_send_request_rejected_reopens_pending(monkeypatch):
    requester_id = UUID("1bc18dc6-e30f-4860-818d-0a5f6fb2b200")
    addressee_id = UUID("b5f8f23d-1d6a-4ac6-b62d-4b8b7d93f971")

    class Existing:
        def __init__(self):
            self.requester_id = addressee_id
            self.addressee_id = requester_id
            self.status = Friendship.STATUS_REJECTED
            self.saved_fields = None

        def save(self, update_fields=None):
            self.saved_fields = update_fields

    existing = Existing()
    monkeypatch.setattr(friendship_views, "_current_user_id", lambda _request: requester_id)
    monkeypatch.setattr(friendship_views, "_find_friendship_pair", lambda *_args, **_kwargs: existing)
    monkeypatch.setattr(friendship_views, "FriendshipSerializer", _mock_serializer)

    request = APIRequestFactory().post(
        "/api/social/send-request/",
        {"user_id": str(addressee_id)},
        format="json",
    )
    response = SendRequestView.as_view()(request)

    assert response.status_code == 200
    assert response.data["detail"] == "Friend request sent"
    assert existing.status == Friendship.STATUS_PENDING
    assert existing.requester_id == requester_id
    assert existing.addressee_id == addressee_id
    assert existing.saved_fields == ["requester_id", "addressee_id", "status", "updated_at"]


def test_send_request_existing_accepted_returns_200(monkeypatch):
    requester_id = UUID("1bc18dc6-e30f-4860-818d-0a5f6fb2b200")
    addressee_id = UUID("b5f8f23d-1d6a-4ac6-b62d-4b8b7d93f971")
    existing = SimpleNamespace(
        requester_id=requester_id,
        addressee_id=addressee_id,
        status=Friendship.STATUS_ACCEPTED,
    )

    monkeypatch.setattr(friendship_views, "_current_user_id", lambda _request: requester_id)
    monkeypatch.setattr(friendship_views, "_find_friendship_pair", lambda *_args, **_kwargs: existing)
    monkeypatch.setattr(friendship_views, "FriendshipSerializer", _mock_serializer)

    request = APIRequestFactory().post(
        "/api/social/send-request/",
        {"user_id": str(addressee_id)},
        format="json",
    )
    response = SendRequestView.as_view()(request)

    assert response.status_code == 200
    assert response.data["detail"] == "You are already friends"

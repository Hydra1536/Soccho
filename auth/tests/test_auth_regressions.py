from types import SimpleNamespace
from urllib.parse import parse_qs

import pytest
from rest_framework.test import APIRequestFactory

pytest.importorskip("axes")

from apps.otp import views as otp_views
from apps.otp.models import OTPCode
from apps.users import views as user_views


def test_login_view_blocks_unverified_user(monkeypatch):
    user = SimpleNamespace(is_verified=False, password_hash="unused")
    monkeypatch.setattr(user_views, "_get_user_by_email", lambda *_args, **_kwargs: user)

    request = APIRequestFactory().post(
        "/api/auth/login/",
        {"email": "user@example.com", "password": "pass12345"},
        format="json",
    )

    response = user_views.LoginView.as_view()(request)

    assert response.status_code == 403
    assert response.data == {"detail": "Account is not verified. Please verify the OTP code first."}


def test_verify_otp_marks_user_verified_for_register(monkeypatch):
    class DummyUser:
        def __init__(self):
            self.is_verified = False
            self.saved_fields = None

        def save(self, update_fields=None):
            self.saved_fields = update_fields

    class DummyOTP:
        def __init__(self):
            self.is_used = False
            self.saved_fields = None

        def save(self, update_fields=None):
            self.saved_fields = update_fields

    class DummyOTPQuerySet:
        def __init__(self, otp):
            self.otp = otp

        def order_by(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.otp

    user = DummyUser()
    otp = DummyOTP()

    monkeypatch.setattr(otp_views, "_get_user_by_email", lambda *_args, **_kwargs: user)
    monkeypatch.setattr(otp_views.OTPCode.objects, "filter", lambda **_kwargs: DummyOTPQuerySet(otp))
    monkeypatch.setattr(otp_views, "_issue_tokens", lambda *_args, **_kwargs: ("access-token", "refresh-token"))

    request = APIRequestFactory().post(
        "/api/auth/otp/verify/",
        {"email": "user@example.com", "code": "123456", "context": OTPCode.CONTEXT_REGISTER},
        format="json",
    )

    response = otp_views.VerifyOTPView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {"access": "access-token", "refresh": "refresh-token"}
    assert otp.is_used is True
    assert otp.saved_fields == ["is_used"]
    assert user.is_verified is True
    assert user.saved_fields == ["is_verified"]


def test_register_view_returns_delivery_error_when_email_send_fails(monkeypatch):
    monkeypatch.setattr(user_views, "_get_user_by_email", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(user_views, "_get_user_by_username", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        user_views.User.objects,
        "create",
        lambda **kwargs: SimpleNamespace(id="user-1", username=kwargs["username"]),
    )
    monkeypatch.setattr(user_views, "generate_otp", lambda *_args, **_kwargs: "123456")
    monkeypatch.setattr(
        user_views,
        "_send_otp_email",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("email send failed")),
    )

    request = APIRequestFactory().post(
        "/api/auth/register/",
        {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "pass12345",
            "confirm_password": "pass12345",
        },
        format="json",
    )

    response = user_views.RegisterView.as_view()(request)

    assert response.status_code == 503
    assert response.data == {"detail": "Could not send the verification code right now"}


def test_register_view_resends_otp_for_existing_unverified_user(monkeypatch):
    class DummyUser:
        def __init__(self):
            self.id = "user-1"
            self.username = "old_name"
            self.password_hash = "old_hash"
            self.is_verified = False
            self.saved_fields = None

        def save(self, update_fields=None):
            self.saved_fields = update_fields

    class DummyFilterResult:
        def __init__(self):
            self.updated_kwargs = None

        def update(self, **kwargs):
            self.updated_kwargs = kwargs
            return 1

    user = DummyUser()
    pending_otps = DummyFilterResult()

    monkeypatch.setattr(user_views, "_get_user_by_email", lambda *_args, **_kwargs: user)
    monkeypatch.setattr(user_views, "_get_user_by_username", lambda *_args, **_kwargs: user)
    monkeypatch.setattr(user_views.OTPCode.objects, "filter", lambda **_kwargs: pending_otps)
    monkeypatch.setattr(user_views, "generate_otp", lambda *_args, **_kwargs: "654321")
    monkeypatch.setattr(user_views, "_send_otp_email", lambda *_args, **_kwargs: None)

    request = APIRequestFactory().post(
        "/api/auth/register/",
        {
            "username": "new_name",
            "email": "user@example.com",
            "password": "pass12345",
            "confirm_password": "pass12345",
        },
        format="json",
    )

    response = user_views.RegisterView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {"message": "OTP sent successfully"}
    assert user.username == "new_name"
    assert user.is_verified is False
    assert user.saved_fields == ["username", "password_hash", "is_verified"]
    assert pending_otps.updated_kwargs == {"is_used": True}


def test_send_otp_email_posts_formsubmit_payload(monkeypatch):
    captured = {}

    class DummyResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"success":true}'

    def fake_urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["body"] = request.data.decode("utf-8")
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(user_views.urllib_request, "urlopen", fake_urlopen)

    user_views._send_otp_email("person@example.com", "123456", OTPCode.CONTEXT_REGISTER)

    assert captured["url"] == user_views.FORMSUBMIT_OTP_ENDPOINT
    payload = parse_qs(captured["body"])
    assert payload["_cc"] == ["person@example.com"]
    assert payload["_replyto"] == ["person@example.com"]
    assert payload["otp"] == ["123456"]
    assert payload["context"] == [OTPCode.CONTEXT_REGISTER]

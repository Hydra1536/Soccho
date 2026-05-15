from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

pytest.importorskip("axes")

from apps.users import views


def test_register_view_accepts_drf_request_with_axes_dispatch(monkeypatch):
    def fake_get_or_create(*_args, **_kwargs):
        return SimpleNamespace(id="user-1", username="reza"), True

    monkeypatch.setattr(views.User.objects, "get_or_create", fake_get_or_create)
    monkeypatch.setattr(views, "generate_otp", lambda *_args, **_kwargs: "123456")
    monkeypatch.setattr(views, "_send_otp_email", lambda *_args, **_kwargs: None)

    request = APIRequestFactory().post(
        "/api/auth/register/",
        {
            "username": "reza2",
            "email": "rezaul21301019@gmail.com",
            "password": "reza21234",
            "confirm_password": "reza21234",
        },
        format="json",
    )

    response = views.RegisterView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {"message": "OTP sent successfully"}

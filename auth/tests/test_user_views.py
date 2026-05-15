from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

pytest.importorskip("axes")

from apps.users import views


def test_axes_protected_skips_decoration_when_disabled(settings):
    settings.AXES_ENABLED = False

    class DummyView:
        pass

    assert views._axes_protected(DummyView) is DummyView


def test_axes_protected_applies_decoration_when_enabled(monkeypatch, settings):
    settings.AXES_ENABLED = True

    def fake_method_decorator(_decorator, name):
        assert name == "dispatch"

        def apply(view_cls):
            view_cls.axes_wrapped = True
            return view_cls

        return apply

    monkeypatch.setattr(views, "method_decorator", fake_method_decorator)

    class DummyView:
        pass

    wrapped = views._axes_protected(DummyView)

    assert wrapped is DummyView
    assert wrapped.axes_wrapped is True


def test_register_view_accepts_drf_request_without_axes(monkeypatch):
    monkeypatch.setattr(views, "_get_user_by_email", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(views, "_get_user_by_username", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        views.User.objects,
        "create",
        lambda **kwargs: SimpleNamespace(id="user-1", username=kwargs["username"]),
    )
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

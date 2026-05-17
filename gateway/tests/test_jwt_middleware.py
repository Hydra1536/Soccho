from app.middleware.auth_exemptions import should_skip_auth


def test_should_skip_auth_for_preflight_options():
    assert should_skip_auth("OPTIONS", "/api/auth/otp/verify/") is True
    assert should_skip_auth("options", "/api/any/protected/path") is True


def test_should_skip_auth_for_otp_verify_path():
    assert should_skip_auth("POST", "/api/auth/otp/verify/") is True


def test_should_skip_auth_for_auth_health_path():
    assert should_skip_auth("GET", "/api/auth/health/") is True


def test_should_not_skip_auth_for_other_protected_paths():
    assert should_skip_auth("POST", "/api/social/feed/") is False

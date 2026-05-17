def test_gateway_imports():
    from app.main import app
    assert app.title == 'Soccho Gateway'


def test_gateway_pydantic_settings_consistency():
    from app.config import Settings
    s = Settings()
    assert isinstance(s.auth_http_base_url, str)
    assert bool(s.gateway_secret_key)

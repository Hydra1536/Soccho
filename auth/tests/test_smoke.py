def test_smoke_import_settings():
    import auth_service.settings as settings
    assert settings.ROOT_URLCONF == 'auth_service.urls'

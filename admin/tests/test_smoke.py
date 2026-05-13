def test_smoke_import_settings():
    import admin_service.settings as settings
    assert settings.ROOT_URLCONF == 'admin_service.urls'

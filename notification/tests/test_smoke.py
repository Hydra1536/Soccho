def test_smoke_import_settings():
    import notification_service.settings as settings
    assert settings.ROOT_URLCONF == 'notification_service.urls'

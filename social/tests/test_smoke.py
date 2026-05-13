def test_smoke_import_settings():
    import social_service.settings as settings
    assert settings.ROOT_URLCONF == 'social_service.urls'

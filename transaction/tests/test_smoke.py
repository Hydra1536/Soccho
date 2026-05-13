def test_smoke_import_settings():
    import transaction_service.settings as settings
    assert settings.ROOT_URLCONF == 'transaction_service.urls'

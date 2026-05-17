import os

import httpx

from keepalive import worker


def test_targets_from_env_parses_csv(monkeypatch):
    monkeypatch.setenv("KEEPALIVE_TARGETS", "https://a/health, https://b/health ,,")
    targets = worker._targets_from_env()
    assert targets == ["https://a/health", "https://b/health"]


def test_env_bool_defaults_and_true_values(monkeypatch):
    monkeypatch.delenv("KEEPALIVE_ENABLED", raising=False)
    assert worker._env_bool("KEEPALIVE_ENABLED", True) is True
    monkeypatch.setenv("KEEPALIVE_ENABLED", "yes")
    assert worker._env_bool("KEEPALIVE_ENABLED", False) is True


def test_probe_target_handles_request_error(monkeypatch):
    class BrokenClient:
        def get(self, _url):
            req = httpx.Request("GET", "https://example.com/health")
            raise httpx.ConnectError("failed", request=req)

    # No exception should escape the probe function.
    worker._probe_target(BrokenClient(), "https://example.com/health")


def test_default_targets_contains_all_services():
    defaults = worker._default_targets()
    assert "soccho-gateway.onrender.com/healthz" in defaults
    assert "soccho-auth.onrender.com/api/auth/health/" in defaults
    assert "soccho-social.onrender.com/health/" in defaults
    assert "soccho-transaction.onrender.com/health/" in defaults
    assert "soccho-notification.onrender.com/health/" in defaults

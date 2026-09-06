"""Regression tests for API Key authentication.

Ensures that when BITNET_API_KEY is configured in the environment,
endpoints enforce opt-in authentication using constant-time string comparison
and correctly reject unauthorized access.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from bitnet_launcher.api import app

# Use a test client that doesn't follow redirects or anything unusual
client = TestClient(app)


@pytest.fixture
def api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to set a test API key in the environment safely."""
    monkeypatch.setenv("BITNET_API_KEY", "test-secret-key-123")


def test_models_no_auth_required_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """If BITNET_API_KEY is not set, the endpoint should not require auth."""
    # Ensure env var is not set safely
    monkeypatch.delenv("BITNET_API_KEY", raising=False)

    with patch("bitnet_launcher.api.discover_models") as mock_discover:
        mock_discover.return_value = []
        response = client.get("/models")
        assert response.status_code == 200
        assert response.json() == []


def test_models_auth_missing_header_rejected(api_key_env: None) -> None:
    """If BITNET_API_KEY is set, requests without X-API-Key should be 401."""
    response = client.get("/models")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API Key"}


def test_models_auth_invalid_key_rejected(api_key_env: None) -> None:
    """If BITNET_API_KEY is set, requests with an invalid X-API-Key should be 401."""
    response = client.get("/models", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API Key"}


def test_models_auth_valid_key_accepted(api_key_env: None) -> None:
    """If BITNET_API_KEY is set, requests with a valid X-API-Key should be 200."""
    with patch("bitnet_launcher.api.discover_models") as mock_discover:
        mock_discover.return_value = []
        response = client.get("/models", headers={"X-API-Key": "test-secret-key-123"})
        assert response.status_code == 200
        assert response.json() == []


def test_chat_start_auth_valid_key_accepted(api_key_env: None) -> None:
    """Ensure sensitive POST endpoints also enforce authentication correctly."""
    # Test rejection first
    resp_unauth = client.post("/chat/start", json={"model_name": "unknown"})
    assert resp_unauth.status_code == 401

    # Test acceptance
    with patch("bitnet_launcher.api.discover_models") as mock_discover:
        mock_discover.return_value = []
        resp_auth = client.post(
            "/chat/start",
            json={"model_name": "unknown"},
            headers={"X-API-Key": "test-secret-key-123"},
        )
        # Should return 404 because model 'unknown' is not found,
        # which means it bypassed the 401 auth check successfully.
        assert resp_auth.status_code == 404

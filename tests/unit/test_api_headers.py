"""Tests for security headers in the FastAPI server."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from bitnet_launcher.api import app

client = TestClient(app)


def test_security_headers_present() -> None:
    """Ensure all responses include strict security headers."""
    with patch("bitnet_launcher.api.discover_models") as mock_discover:
        mock_discover.return_value = []
        response = client.get("/models")
        assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")

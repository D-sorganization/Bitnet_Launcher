"""Regression tests for the CORS restrictions on the local API.

The API is served on loopback and must only be readable/callable from the
launcher's own web client. Any other origin — including unrelated services
that happen to be served on loopback port 80 — must not receive CORS headers.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from bitnet_launcher.api import app

client = TestClient(app)


def test_preflight_from_launcher_origin_is_allowed() -> None:
    """A preflight from the launcher's own origin gets explicit CORS approval."""
    response = client.options(
        "/models",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200, response.text
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:8000"
    )
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_external_origin_gets_no_cors_headers() -> None:
    """A malicious website must not be able to read the API cross-origin."""
    response = client.get("/models", headers={"Origin": "http://evil.example.com"})
    # The request itself is still served (CORS is browser-enforced), but the
    # response must not authorize the external origin to read it.
    assert "access-control-allow-origin" not in response.headers


def test_port80_loopback_origin_gets_no_cors_headers() -> None:
    """Loopback port-80 pages are unrelated local services, not the launcher.

    An unrelated local HTTP service on port 80 must not be granted
    cross-origin access merely because it runs on the same host.
    """
    response = client.get("/models", headers={"Origin": "http://localhost"})
    assert "access-control-allow-origin" not in response.headers

    response = client.get("/models", headers={"Origin": "http://127.0.0.1"})
    assert "access-control-allow-origin" not in response.headers


def test_preflight_from_external_origin_is_not_authorized() -> None:
    """Preflight requests from external origins must not be approved."""
    response = client.options(
        "/chat/start",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    # Disallowed preflights are rejected by CORSMiddleware.
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

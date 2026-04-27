"""Tests for the FastAPI server."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from bitnet_launcher.api import app
from bitnet_launcher.models import ModelInfo

client = TestClient(app)


@patch("bitnet_launcher.api.discover_models")
def test_list_models_empty(mock_discover: Any) -> None:
    """Test listing models when none are found."""
    mock_discover.return_value = []
    response = client.get("/models")
    assert response.status_code == 200
    assert response.json() == []


@patch("bitnet_launcher.api.discover_models")
def test_list_models(mock_discover: Any, tmp_path: Any) -> None:
    """Test listing discovered models."""
    model_path = tmp_path / "bitnet_b1_58-3B" / "ggml-model-i2_s.gguf"
    mock_discover.return_value = [
        ModelInfo(name="bitnet_b1_58-3B", path=model_path, size_bytes=1024),
    ]

    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "bitnet_b1_58-3B"
    assert data[0]["path"] == str(model_path)
    assert data[0]["size_bytes"] == 1024


@patch("bitnet_launcher.api.discover_models")
def test_start_chat_not_found(mock_discover: Any) -> None:
    """Test starting chat with an unknown model returns 404."""
    mock_discover.return_value = []
    response = client.post("/chat/start", params={"model_name": "unknown"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Model not found"}


@patch("bitnet_launcher.api.discover_models")
def test_start_chat_success(mock_discover: Any, tmp_path: Any) -> None:
    """Test starting chat with a valid model."""
    model_path = tmp_path / "bitnet_b1_58-3B" / "ggml-model-i2_s.gguf"
    mock_discover.return_value = [
        ModelInfo(name="bitnet_b1_58-3B", path=model_path, size_bytes=1024),
    ]

    response = client.post("/chat/start", params={"model_name": "bitnet_b1_58-3B"})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Started session with bitnet_b1_58-3B",
    }

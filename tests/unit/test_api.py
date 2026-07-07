"""Tests for the FastAPI server."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

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
    response = client.post("/chat/start", json={"model_name": "unknown"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Model not found"}


@patch("bitnet_launcher.api.LocalLlamaRunner.stream_stdout")
@patch("bitnet_launcher.api.LocalLlamaRunner.start")
@patch("bitnet_launcher.api.discover_models")
def test_start_chat_success(
    mock_discover: Any, mock_start: Any, mock_stream: Any, tmp_path: Any
) -> None:
    """Test starting chat with a valid model."""

    # Ensure registry is clear before the test
    from bitnet_launcher.api import active_runners

    active_runners.clear()

    model_path = tmp_path / "bitnet_b1_58-3B" / "ggml-model-i2_s.gguf"
    mock_discover.return_value = [
        ModelInfo(name="bitnet_b1_58-3B", path=model_path, size_bytes=1024),
    ]

    async def mock_generator() -> AsyncGenerator[str, None]:
        yield "mock output chunk"

    mock_stream.return_value = mock_generator()

    with client.stream(
        "POST", "/chat/start", json={"model_name": "bitnet_b1_58-3B"}
    ) as response:
        assert response.status_code == 200
        mock_start.assert_called_once()
        # We can read the stream to verify output
        content = list(response.iter_text())
        assert "".join(content) == "data: mock output chunk\n\n"

    # Test the send message endpoint with a mock runner
    with patch("bitnet_launcher.api.active_runners") as mock_runners:
        mock_runner = AsyncMock()
        mock_runners.get.return_value = mock_runner
        send_resp = client.post(
            "/chat/send", json={"model_name": "bitnet_b1_58-3B", "message": "hello"}
        )
        assert send_resp.status_code == 200
        mock_runner.send_message.assert_called_once_with("hello")


def test_start_chat_concurrency_limit(tmp_path: Any) -> None:
    """Test starting multiple chats returns 429."""
    from bitnet_launcher.api import active_runners

    active_runners.clear()

    # Pre-fill registry
    active_runners["other_model"] = AsyncMock()

    response = client.post("/chat/start", json={"model_name": "bitnet_b1_58-3B"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many active chat sessions"}


def test_start_chat_already_running(tmp_path: Any) -> None:
    """Test starting same model twice returns 409."""
    from bitnet_launcher.api import active_runners

    active_runners.clear()

    # Pre-fill registry with same model
    active_runners["bitnet_b1_58-3B"] = AsyncMock()

    response = client.post("/chat/start", json={"model_name": "bitnet_b1_58-3B"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Model already running"}

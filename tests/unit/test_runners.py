from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bitnet_launcher.models import ModelInfo
from bitnet_launcher.runners import LocalLlamaRunner


@pytest.fixture
def mock_model():
    return ModelInfo(
        name="Test Model",
        path=Path("/fake/test.gguf"),
        size_bytes=1000000,
    )


@pytest.mark.asyncio
@patch("bitnet_launcher.runners.build_command")
async def test_local_runner_lifecycle(mock_build_cmd, mock_model):
    mock_build_cmd.return_value = ["dummy", "cmd"]
    runner = LocalLlamaRunner(Path("/fake/llama"), Path("/fake/root"))

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = AsyncMock()
        mock_proc.stdout = AsyncMock()

        # Simulate stdout returning some data then EOF
        mock_proc.stdout.read.side_effect = [b"hello ", b"world", b""]
        mock_proc.wait = AsyncMock()
        mock_exec.return_value = mock_proc

        await runner.start(mock_model, {"prompt": "test"})
        assert runner._process is not None

        # Test sending message
        await runner.send_message("test message")
        mock_proc.stdin.write.assert_called_with(b"test message\n")

        # Test streaming
        chunks = []
        async for chunk in runner.stream_stdout():
            chunks.append(chunk)
        assert chunks == ["hello ", "world"]

        # Test stop
        await runner.stop()
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_local_runner_start_already_running(mock_model):
    runner = LocalLlamaRunner(Path("/fake/llama"), Path("/fake/root"))
    runner._process = MagicMock()
    runner._process.returncode = None

    with pytest.raises(RuntimeError, match="already running"):
        await runner.start(mock_model, {})


@pytest.mark.asyncio
async def test_local_runner_stop_kill_fallback():
    runner = LocalLlamaRunner(Path("/fake/llama"), Path("/fake/root"))
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.wait = AsyncMock(side_effect=TimeoutError())
    runner._process = mock_proc

    await runner.stop()
    mock_proc.terminate.assert_called_once()
    mock_proc.kill.assert_called_once()

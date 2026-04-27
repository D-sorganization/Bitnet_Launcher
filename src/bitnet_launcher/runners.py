"""Decoupled runner for local Llama/BitNet processes."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from bitnet_launcher.config import InferenceConfig
from bitnet_launcher.models import ModelInfo
from bitnet_launcher.terminal import build_command

logger = logging.getLogger(__name__)


class LocalLlamaRunner:
    """Async wrapper around the llama-cli process for BitNet models.

    This provides a decoupled way to run chat inference without PyQt dependencies,
    making it usable from FastAPI or other asyncio contexts.
    """

    def __init__(
        self,
        llama_cli: Path,
        bitnet_root: Path,
    ) -> None:
        self._llama_cli = llama_cli
        self._bitnet_root = bitnet_root
        self._process: asyncio.subprocess.Process | None = None

    async def start(self, model: ModelInfo, config: InferenceConfig) -> None:
        """Start the llama-cli process."""
        if self._process is not None and self._process.returncode is None:
            raise RuntimeError("Process is already running")

        cmd = build_command(self._llama_cli, model, config)
        logger.info("Starting local runner: %s", cmd)

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self._bitnet_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )

    async def send_message(self, message: str) -> None:
        """Send a message to the running process."""
        if self._process is None or self._process.returncode is not None:
            raise RuntimeError("Process is not running")
        if self._process.stdin is None:
            raise RuntimeError("Process stdin is not open")

        self._process.stdin.write((message + "\n").encode("utf-8"))
        await self._process.stdin.drain()

    async def stream_stdout(self) -> AsyncGenerator[str, None]:
        """Stream stdout chunks from the process."""
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Process stdout is not available")

        while True:
            chunk = await self._process.stdout.read(1024)
            if not chunk:
                break
            yield chunk.decode("utf-8", errors="replace")

    async def stop(self) -> None:
        """Terminate the process."""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None

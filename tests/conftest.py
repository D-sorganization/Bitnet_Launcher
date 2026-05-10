"""Shared pytest fixtures for BitNet Launcher tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bitnet_launcher.config import BitnetConfig, InferenceConfig
from bitnet_launcher.models import ModelInfo


@pytest.fixture()
def default_inference_config() -> InferenceConfig:
    """Return an InferenceConfig with all defaults."""
    return InferenceConfig()


@pytest.fixture()
def default_bitnet_config(tmp_path: Path) -> BitnetConfig:
    """Return a BitnetConfig pointing at a temporary directory."""
    return BitnetConfig(
        bitnet_root=tmp_path,
        llama_cli=tmp_path / "llama-cli",
        models_dir=tmp_path / "models",
        wt_exe="wt.exe",
    )


@pytest.fixture()
def sample_model(tmp_path: Path) -> ModelInfo:
    """Return a ModelInfo pointing at a real (stub) .gguf file."""
    gguf = tmp_path / "model.gguf"
    gguf.write_bytes(b"\x00" * 2_000_000)  # large enough to pass MIN_MODEL_BYTES
    return ModelInfo(name="test-model", path=gguf, size_bytes=2_000_000)

"""Shared pytest fixtures for BitNet Launcher tests.

Per FLEET_TESTING_STANDARDS.md §5, environment variables that affect
heavy C-extension / GUI imports MUST be set BEFORE those modules are
imported. PyQt6 reads QT_QPA_PLATFORM at import time, so this block
must remain at the very top of the file.
"""

from __future__ import annotations

import os

# --- §5 env block: must run before any heavy import ---------------------
# C-extension thread safety (xdist worker crash hygiene).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# matplotlib headless backend (set before any matplotlib import).
os.environ.setdefault("MPLBACKEND", "Agg")

# Qt headless backend — REQUIRED for this repo because src/bitnet_launcher
# pulls in PyQt6 indirectly through several test imports.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# ------------------------------------------------------------------------

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from bitnet_launcher.config import BitnetConfig, InferenceConfig  # noqa: E402
from bitnet_launcher.models import ModelInfo  # noqa: E402


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

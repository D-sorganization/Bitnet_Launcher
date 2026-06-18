"""Configuration dataclasses for BitNet Launcher.

Provides :class:`BitnetConfig` for path configuration and
:class:`InferenceConfig` for inference hyperparameters.  Both classes
enforce Design-by-Contract invariants in ``__post_init__``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_BITNET_ROOT = Path("/home/dieterolson/BitNet")
_DEFAULT_WT_EXE = "/mnt/c/Users/diete/AppData/Local/Microsoft/WindowsApps/wt.exe"


@dataclass
class BitnetConfig:
    """Filesystem paths required to run BitNet models.

    Parameters
    ----------
    bitnet_root:
        Root of the BitNet checkout (contains ``build/``, ``models/``).
    llama_cli:
        Path to the compiled ``llama-cli`` binary.
    models_dir:
        Directory that contains one sub-directory per model.
    wt_exe:
        Absolute path (or interop name) of ``wt.exe``.
    """

    bitnet_root: Path = field(default_factory=lambda: _DEFAULT_BITNET_ROOT)
    llama_cli: Path = field(
        default_factory=lambda: _DEFAULT_BITNET_ROOT / "build" / "bin" / "llama-cli"
    )
    models_dir: Path = field(default_factory=lambda: _DEFAULT_BITNET_ROOT / "models")
    wt_exe: str = _DEFAULT_WT_EXE

    def __post_init__(self) -> None:
        """Validate all path fields."""
        if not isinstance(self.bitnet_root, Path):
            raise TypeError(
                f"bitnet_root must be a Path, got {type(self.bitnet_root).__name__}"
            )
        if not isinstance(self.llama_cli, Path):
            raise TypeError(
                f"llama_cli must be a Path, got {type(self.llama_cli).__name__}"
            )
        if not isinstance(self.models_dir, Path):
            raise TypeError(
                f"models_dir must be a Path, got {type(self.models_dir).__name__}"
            )
        if not isinstance(self.wt_exe, str):
            raise TypeError(f"wt_exe must be a str, got {type(self.wt_exe).__name__}")
        if not self.wt_exe.strip():
            raise ValueError("wt_exe must not be blank")
        logger.debug("BitnetConfig validated: bitnet_root=%s", self.bitnet_root)


@dataclass
class InferenceConfig:
    """Inference hyperparameters passed to ``llama-cli``.

    Parameters
    ----------
    threads:
        Number of CPU threads (>= 1).
    ctx_size:
        Context window in tokens (>= 512).
    temperature:
        Sampling temperature in [0.0, 2.0].
    n_predict:
        Maximum tokens per response; -1 means unlimited.
    system_prompt:
        Non-blank system-role instruction string.
    """

    threads: int = 4
    ctx_size: int = 2048
    temperature: float = 0.8
    n_predict: int = -1
    system_prompt: str = "You are a helpful assistant."

    def __post_init__(self) -> None:  # noqa: C901
        """Enforce DbC invariants on all fields."""
        if not isinstance(self.threads, int):
            raise TypeError(f"threads must be int, got {type(self.threads).__name__}")
        if self.threads < 1:
            raise ValueError(f"threads must be >= 1, got {self.threads}")

        if not isinstance(self.ctx_size, int):
            raise TypeError(f"ctx_size must be int, got {type(self.ctx_size).__name__}")
        if self.ctx_size < 512:
            raise ValueError(f"ctx_size must be >= 512, got {self.ctx_size}")

        if not isinstance(self.temperature, int | float):
            raise TypeError(
                f"temperature must be numeric, got {type(self.temperature).__name__}"
            )
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(
                f"temperature must be in [0.0, 2.0], got {self.temperature}"
            )

        if not isinstance(self.n_predict, int):
            raise TypeError(
                f"n_predict must be int, got {type(self.n_predict).__name__}"
            )
        if self.n_predict < -1:
            raise ValueError(f"n_predict must be >= -1, got {self.n_predict}")

        if not isinstance(self.system_prompt, str):
            raise TypeError(
                f"system_prompt must be str, got {type(self.system_prompt).__name__}"
            )
        if not self.system_prompt.strip():
            raise ValueError("system_prompt must not be blank")
        if len(self.system_prompt) > 4096:
            raise ValueError("system_prompt must not exceed 4096 characters")

        logger.debug(
            "InferenceConfig validated: threads=%d ctx=%d temp=%.2f",
            self.threads,
            self.ctx_size,
            self.temperature,
        )

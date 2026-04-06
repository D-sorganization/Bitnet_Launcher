"""Terminal launch utilities for BitNet Launcher.

Provides pure functions for building the llama-cli argument list and
opening a new Windows Terminal tab with an interactive model session.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from bitnet_launcher.config import InferenceConfig
from bitnet_launcher.models import ModelInfo

logger = logging.getLogger(__name__)


def build_command(
    llama_cli: Path,
    model: ModelInfo,
    config: InferenceConfig,
) -> list[str]:
    """Build the ``llama-cli`` argv list for the given model and config.

    Parameters
    ----------
    llama_cli:
        Path to the ``llama-cli`` binary.
    model:
        The model to load.
    config:
        Inference hyperparameters.

    Returns
    -------
    list[str]
        Full argument vector including the executable path at index 0.

    Raises
    ------
    TypeError
        If any argument has the wrong type.
    """
    if not isinstance(llama_cli, Path):
        raise TypeError(f"llama_cli must be a Path, got {type(llama_cli).__name__}")
    if not isinstance(model, ModelInfo):
        raise TypeError(f"model must be a ModelInfo, got {type(model).__name__}")
    if not isinstance(config, InferenceConfig):
        raise TypeError(
            f"config must be an InferenceConfig, got {type(config).__name__}"
        )

    cmd: list[str] = [
        str(llama_cli),
        "-m",
        str(model.path),
        "-t",
        str(config.threads),
        "-c",
        str(config.ctx_size),
        "--temp",
        str(config.temperature),
        "-b",
        "1",
        "-ngl",
        "0",
        "-p",
        config.system_prompt,
        "-cnv",
    ]

    if config.n_predict != -1:
        cmd += ["-n", str(config.n_predict)]

    logger.debug("Built command for model %s: %s", model.name, cmd)
    return cmd


def launch_terminal(
    llama_cli: Path,
    model: ModelInfo,
    config: InferenceConfig,
    bitnet_root: Path,
    wt_exe: str,
) -> None:
    """Open a new Windows Terminal tab running the model interactively.

    The session keeps the terminal open after the model exits (``exec bash``).
    Falls back to plain ``wt.exe`` if the configured path is not found.

    Parameters
    ----------
    llama_cli:
        Path to the ``llama-cli`` binary.
    model:
        The model to run.
    config:
        Inference hyperparameters.
    bitnet_root:
        Working directory for the bash session.
    wt_exe:
        Absolute path (or interop name) of ``wt.exe``.

    Raises
    ------
    TypeError
        If any argument has the wrong type.
    ValueError
        If ``wt_exe`` is blank.
    FileNotFoundError
        If Windows Terminal cannot be located at all.
    """
    if not isinstance(llama_cli, Path):
        raise TypeError(f"llama_cli must be a Path, got {type(llama_cli).__name__}")
    if not isinstance(model, ModelInfo):
        raise TypeError(f"model must be a ModelInfo, got {type(model).__name__}")
    if not isinstance(config, InferenceConfig):
        raise TypeError(
            f"config must be an InferenceConfig, got {type(config).__name__}"
        )
    if not isinstance(bitnet_root, Path):
        raise TypeError(f"bitnet_root must be a Path, got {type(bitnet_root).__name__}")
    if not isinstance(wt_exe, str):
        raise TypeError(f"wt_exe must be a str, got {type(wt_exe).__name__}")
    if not wt_exe.strip():
        raise ValueError("wt_exe must not be blank")

    cmd = build_command(llama_cli, model, config)
    bash_cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    full_bash = (
        f'cd "{bitnet_root}" && {bash_cmd}; '
        'echo; echo "--- session ended ---"; exec bash'
    )

    def _try_launch(wt: str) -> None:
        subprocess.Popen(
            [
                wt,
                "new-tab",
                "--title",
                f"BitNet: {model.name}",
                "bash",
                "-c",
                full_bash,
            ],
            close_fds=True,
        )

    try:
        _try_launch(wt_exe)
        logger.info("Opened terminal tab for model: %s", model.name)
    except FileNotFoundError:
        logger.warning(
            "wt.exe not found at %s — retrying with interop 'wt.exe'", wt_exe
        )
        _try_launch("wt.exe")

"""HuggingFace model catalog and download utilities for BitNet-compatible models.

Provides :data:`CATALOG` listing all supported BitNet models and
:func:`download_model` which drives ``setup_env.py`` to download and
quantize a model from HuggingFace Hub.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HubModel:
    """Immutable descriptor for a HuggingFace-hosted BitNet-compatible model.

    Parameters
    ----------
    repo_id:
        HuggingFace repository identifier, e.g. ``"microsoft/BitNet-b1.58-2B-4T"``.
    name:
        Local folder name used by BitNet's setup_env.py,
        e.g. ``"BitNet-b1.58-2B-4T"``.
    description:
        Human-readable summary of the model.
    params:
        Parameter count string, e.g. ``"2.4B"``.
    size_gb:
        Approximate download size in gigabytes.
    tags:
        List of category tags, e.g. ``["official"]``.
    """

    repo_id: str
    name: str
    description: str
    params: str
    size_gb: float
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate all fields."""
        if not isinstance(self.repo_id, str) or not self.repo_id.strip():
            raise ValueError("repo_id must be a non-blank str")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-blank str")
        if not isinstance(self.description, str):
            raise TypeError(
                f"description must be str, got {type(self.description).__name__}"
            )
        if not isinstance(self.params, str) or not self.params.strip():
            raise ValueError("params must be a non-blank str")
        if not isinstance(self.size_gb, (int, float)):
            raise TypeError(
                f"size_gb must be numeric, got {type(self.size_gb).__name__}"
            )
        if self.size_gb <= 0:
            raise ValueError(f"size_gb must be > 0, got {self.size_gb}")
        if not isinstance(self.tags, list):
            raise TypeError(f"tags must be a list, got {type(self.tags).__name__}")


# ---------------------------------------------------------------------------
# Model catalog (all models from BitNet's setup_env.py + Falcon-E extras)
# ---------------------------------------------------------------------------

CATALOG: list[HubModel] = [
    HubModel(
        "microsoft/BitNet-b1.58-2B-4T",
        "BitNet-b1.58-2B-4T",
        "Official Microsoft 2.4B BitNet model, trained on 4T tokens",
        "2.4B",
        1.2,
        ["official"],
    ),
    HubModel(
        "1bitLLM/bitnet_b1_58-large",
        "bitnet_b1_58-large",
        "0.7B BitNet large reference model",
        "0.7B",
        0.26,
        ["reference"],
    ),
    HubModel(
        "1bitLLM/bitnet_b1_58-3B",
        "bitnet_b1_58-3B",
        "3B BitNet reference model",
        "3B",
        1.1,
        ["reference"],
    ),
    HubModel(
        "HF1BitLLM/Llama3-8B-1.58-100B-tokens",
        "Llama3-8B-1.58-100B-tokens",
        "Llama 3 8B fine-tuned to 1.58-bit on 100B tokens",
        "8B",
        4.0,
        ["llama3"],
    ),
    HubModel(
        "tiiuae/Falcon3-1B-Instruct-1.58bit",
        "Falcon3-1B-Instruct-1.58bit",
        "Falcon3 1B instruct model at 1.58-bit",
        "1B",
        0.4,
        ["falcon", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon3-1B-1.58bit",
        "Falcon3-1B-1.58bit",
        "Falcon3 1B base at 1.58-bit",
        "1B",
        0.4,
        ["falcon"],
    ),
    HubModel(
        "tiiuae/Falcon3-3B-Instruct-1.58bit",
        "Falcon3-3B-Instruct-1.58bit",
        "Falcon3 3B instruct model at 1.58-bit",
        "3B",
        1.2,
        ["falcon", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon3-3B-1.58bit",
        "Falcon3-3B-1.58bit",
        "Falcon3 3B base at 1.58-bit",
        "3B",
        1.2,
        ["falcon"],
    ),
    HubModel(
        "tiiuae/Falcon3-7B-Instruct-1.58bit",
        "Falcon3-7B-Instruct-1.58bit",
        "Falcon3 7B instruct model at 1.58-bit",
        "7B",
        2.8,
        ["falcon", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon3-7B-1.58bit",
        "Falcon3-7B-1.58bit",
        "Falcon3 7B base at 1.58-bit",
        "7B",
        2.8,
        ["falcon"],
    ),
    HubModel(
        "tiiuae/Falcon3-10B-Instruct-1.58bit",
        "Falcon3-10B-Instruct-1.58bit",
        "Falcon3 10B instruct model at 1.58-bit",
        "10B",
        3.8,
        ["falcon", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon3-10B-1.58bit",
        "Falcon3-10B-1.58bit",
        "Falcon3 10B base at 1.58-bit",
        "10B",
        3.8,
        ["falcon"],
    ),
    HubModel(
        "tiiuae/Falcon-E-1B-Instruct",
        "Falcon-E-1B-Instruct",
        "Falcon-E 1B instruct (edge-optimised)",
        "1B",
        0.4,
        ["falcon-e", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon-E-1B-Base",
        "Falcon-E-1B-Base",
        "Falcon-E 1B base (edge-optimised)",
        "1B",
        0.4,
        ["falcon-e"],
    ),
    HubModel(
        "tiiuae/Falcon-E-3B-Instruct",
        "Falcon-E-3B-Instruct",
        "Falcon-E 3B instruct (edge-optimised)",
        "3B",
        1.2,
        ["falcon-e", "instruct"],
    ),
    HubModel(
        "tiiuae/Falcon-E-3B-Base",
        "Falcon-E-3B-Base",
        "Falcon-E 3B base (edge-optimised)",
        "3B",
        1.2,
        ["falcon-e"],
    ),
]


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------


def _validate_download_args(
    hub_model: HubModel,
    models_dir: Path,
    bitnet_root: Path,
    on_log: Callable[[str], None],
    on_progress: Callable[[float], None],
) -> None:
    if not isinstance(hub_model, HubModel):
        raise TypeError(f"hub_model must be a HubModel, got {type(hub_model).__name__}")
    if not isinstance(models_dir, Path):
        raise TypeError(f"models_dir must be a Path, got {type(models_dir).__name__}")
    if not isinstance(bitnet_root, Path):
        raise TypeError(f"bitnet_root must be a Path, got {type(bitnet_root).__name__}")
    if not callable(on_log):
        raise TypeError("on_log must be callable")
    if not callable(on_progress):
        raise TypeError("on_progress must be callable")


def download_model(
    hub_model: HubModel,
    models_dir: Path,
    bitnet_root: Path,
    on_log: Callable[[str], None],
    on_progress: Callable[[float], None],
) -> Path:
    """Download and quantize a model using BitNet's ``setup_env.py``.

    Runs::

        python3 setup_env.py --hf-repo <repo_id> -md <models_dir> -q i2_s

    inside *bitnet_root*.  Streams each stdout/stderr line to *on_log* and
    calls *on_progress* with ``0.0`` at start and ``1.0`` on completion.

    Parameters
    ----------
    hub_model:
        Catalog entry describing the model to download.
    models_dir:
        Directory where models are stored (passed as ``-md`` to setup_env.py).
    bitnet_root:
        Root of the BitNet checkout (must contain ``setup_env.py``).
    on_log:
        Callback receiving each line of subprocess output.
    on_progress:
        Callback receiving a float in ``[0.0, 1.0]``.

    Returns
    -------
    Path
        Path to the downloaded model directory (``models_dir / hub_model.name``).

    Raises
    ------
    TypeError
        If any argument has the wrong type.
    ValueError
        If *models_dir* cannot be created or *bitnet_root* does not contain
        ``setup_env.py``.
    RuntimeError
        If ``setup_env.py`` exits with a non-zero return code.
    """
    _validate_download_args(hub_model, models_dir, bitnet_root, on_log, on_progress)

    setup_env = bitnet_root / "setup_env.py"
    if not setup_env.exists():
        raise ValueError(f"setup_env.py not found in bitnet_root: {bitnet_root}")

    models_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3",
        str(setup_env),
        "--hf-repo",
        hub_model.repo_id,
        "-md",
        str(models_dir),
        "-q",
        "i2_s",
    ]
    logger.info("Downloading model %s via: %s", hub_model.name, cmd)
    on_progress(0.0)

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(bitnet_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if process.stdout is not None:
            for line in process.stdout:
                stripped = line.rstrip("\n")
                if stripped:
                    on_log(stripped)
                    logger.debug("download_model: %s", stripped)
        return_code = process.wait()
    except OSError as exc:
        raise RuntimeError(f"Failed to start setup_env.py: {exc}") from exc

    if return_code != 0:
        raise RuntimeError(
            f"setup_env.py exited with code {return_code} for model {hub_model.repo_id}"
        )

    on_progress(1.0)
    dest = models_dir / hub_model.name
    logger.info("Model download complete: %s", dest)
    return dest

"""HuggingFace model catalog and download utilities for BitNet-compatible models.

Provides :data:`CATALOG` listing all supported BitNet models and
:func:`download_model` which drives ``setup_env.py`` to download and
quantize a model from HuggingFace Hub.
"""

from __future__ import annotations

import logging
import os
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
    gguf_file:
        If set, the model is a *prebuilt* GGUF: this is the exact filename to
        pull from *repo_id* (which should be a ``-gguf`` repo) via
        :func:`_download_prebuilt_gguf`, bypassing ``setup_env.py``.  ``None``
        means the model is downloaded + quantized by ``setup_env.py`` instead.
    """

    repo_id: str
    name: str
    description: str
    params: str
    size_gb: float
    tags: list[str] = field(default_factory=list)
    gguf_file: str | None = None

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
        if not isinstance(self.size_gb, int | float):
            raise TypeError(
                f"size_gb must be numeric, got {type(self.size_gb).__name__}"
            )
        if self.size_gb <= 0:
            raise ValueError(f"size_gb must be > 0, got {self.size_gb}")
        if not isinstance(self.tags, list):
            raise TypeError(f"tags must be a list, got {type(self.tags).__name__}")
        if self.gguf_file is not None and (
            not isinstance(self.gguf_file, str) or not self.gguf_file.strip()
        ):
            raise ValueError("gguf_file must be None or a non-blank str")


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
    # OpenBMB BitCPM4-CANN family (1.58-bit ternary QAT, MiniCPM4-based,
    # llama architecture). BitNet's setup_env.py only accepts a fixed
    # --hf-repo allow-list and rejects these, so we pull the *prebuilt* GGUF
    # straight from the -gguf repos (see gguf_file + _download_prebuilt_gguf).
    # We use the TQ2_0 ternary file; the BF16 sibling is the full-precision
    # version and is intentionally not used. size_gb tracks the TQ2_0 download.
    HubModel(
        "openbmb/BitCPM4-CANN-1B-gguf",
        "BitCPM4-CANN-1B",
        "OpenBMB BitCPM4 1B ternary (1.58-bit QAT, MiniCPM4-based); ~97% FP retention",
        "1B",
        0.55,
        ["bitcpm", "ternary"],
        gguf_file="bitcpm4-1b-tq2_0.gguf",
    ),
    HubModel(
        "openbmb/BitCPM4-CANN-3B-gguf",
        "BitCPM4-CANN-3B",
        "OpenBMB BitCPM4 3B ternary (1.58-bit QAT, MiniCPM4-based); ~97% FP retention",
        "3B",
        1.5,
        ["bitcpm", "ternary"],
        gguf_file="bitcpm4-3b-tq2_0.gguf",
    ),
    HubModel(
        "openbmb/BitCPM4-CANN-8B-gguf",
        "BitCPM4-CANN-8B",
        "OpenBMB BitCPM4 8B ternary (1.58-bit QAT, MiniCPM4-based); ~96% FP retention",
        "8B",
        3.6,
        ["bitcpm", "ternary"],
        gguf_file="bitcpm4-8b-tq2_0.gguf",
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

    # Prebuilt-GGUF models (e.g. BitCPM4) are not in setup_env.py's --hf-repo
    # allow-list, so fetch the .gguf directly instead of quantizing.
    if hub_model.gguf_file is not None:
        return _download_prebuilt_gguf(hub_model, models_dir, on_log, on_progress)

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


def _download_prebuilt_gguf(
    hub_model: HubModel,
    models_dir: Path,
    on_log: Callable[[str], None],
    on_progress: Callable[[float], None],
) -> Path:
    """Download a prebuilt ``.gguf`` from a HuggingFace ``-gguf`` repo.

    Used for models that BitNet's ``setup_env.py`` cannot handle because its
    ``--hf-repo`` argument only accepts a fixed allow-list.  Fetches the file
    named by :attr:`HubModel.gguf_file`; if that exact name is absent, falls
    back to the first ``*tq2_0*.gguf`` in the repo (tolerant of casing /
    naming drift across model sizes).  The file is saved into
    ``models_dir / hub_model.name`` so :func:`~bitnet_launcher.models.discover_models`
    finds it automatically.

    Xet transfer is disabled (``HF_HUB_DISABLE_XET``) because it has been
    observed to stall indefinitely on large GGUF blobs; the classic HTTPS CDN
    is used instead.

    Parameters
    ----------
    hub_model:
        Catalog entry; must have a non-``None`` ``gguf_file``.
    models_dir:
        Directory where models are stored.
    on_log:
        Callback receiving human-readable progress lines.
    on_progress:
        Callback receiving ``0.0`` at start and ``1.0`` on completion.

    Returns
    -------
    Path
        Path to the downloaded ``.gguf`` file.

    Raises
    ------
    RuntimeError
        If ``huggingface_hub`` is missing, the repo cannot be listed, no
        ternary ``.gguf`` is found, or the download itself fails.
    """
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is required for prebuilt GGUF downloads; "
            "install it with: pip install 'bitnet-launcher[hub]'"
        ) from exc

    # Xet stalls on large GGUF blobs in some environments — force classic CDN.
    os.environ["HF_HUB_DISABLE_XET"] = "1"

    dest_dir = models_dir / hub_model.name
    dest_dir.mkdir(parents=True, exist_ok=True)

    on_log(f"Resolving GGUF in {hub_model.repo_id} …")
    try:
        repo_files = list_repo_files(hub_model.repo_id)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Failed to list files in {hub_model.repo_id}: {exc}"
        ) from exc

    filename = hub_model.gguf_file
    if filename not in repo_files:
        ternary = [
            f
            for f in repo_files
            if (f_lower := f.lower()).endswith(".gguf") and "tq2_0" in f_lower
        ]
        if not ternary:
            raise RuntimeError(
                f"No TQ2_0 .gguf found in {hub_model.repo_id}; "
                f"available files: {repo_files}"
            )
        on_log(f"'{filename}' not found; using '{ternary[0]}' instead")
        filename = ternary[0]

    on_log(f"Downloading {filename} → {dest_dir} (Xet disabled)…")
    on_progress(0.0)
    try:
        path = hf_hub_download(
            repo_id=hub_model.repo_id,
            filename=filename,
            local_dir=str(dest_dir),
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Failed to download {filename} from {hub_model.repo_id}: {exc}"
        ) from exc

    on_progress(1.0)
    on_log(f"Saved: {path}")
    logger.info("Prebuilt GGUF download complete: %s", path)
    return Path(path)

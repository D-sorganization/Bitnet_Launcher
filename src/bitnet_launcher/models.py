"""Model discovery for BitNet Launcher.

Provides :class:`ModelInfo` and :func:`discover_models` for scanning a
models directory and returning structured information about available
``.gguf`` model files.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_MODEL_BYTES: int = 1_000_000  # skip placeholder / metadata files


def _fmt_bytes(n: int) -> str:
    """Format *n* bytes as a human-readable string.

    Parameters
    ----------
    n:
        Byte count (>= 0).

    Returns
    -------
    str
        Human-readable size string, e.g. ``"1.2 GB"``.
    """
    value: float = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0:
            return f"{value:.0f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


@dataclass(frozen=True)
class ModelInfo:
    """Immutable descriptor for a single discovered model file.

    Parameters
    ----------
    name:
        Human-readable model name (typically the parent directory name).
    path:
        Absolute path to the ``.gguf`` weight file.
    size_bytes:
        File size in bytes.
    """

    name: str
    path: Path
    size_bytes: int

    def __post_init__(self) -> None:
        """Validate fields."""
        if not isinstance(self.name, str):
            raise TypeError(f"name must be str, got {type(self.name).__name__}")
        if not self.name.strip():
            raise ValueError("name must not be blank")
        if not isinstance(self.path, Path):
            raise TypeError(f"path must be a Path, got {type(self.path).__name__}")
        if not isinstance(self.size_bytes, int):
            raise TypeError(
                f"size_bytes must be int, got {type(self.size_bytes).__name__}"
            )
        if self.size_bytes < 0:
            raise ValueError(f"size_bytes must be >= 0, got {self.size_bytes}")

    @property
    def display_name(self) -> str:
        """Return a display string including the formatted file size."""
        return f"{self.name}  ({_fmt_bytes(self.size_bytes)})"


def discover_models(models_dir: Path) -> list[ModelInfo]:
    """Scan *models_dir* for usable ``.gguf`` files.

    Each immediate sub-directory of *models_dir* is treated as a model
    family.  Within each family directory the function prefers files
    whose names contain ``i2_s`` (BitNet optimised quantisation); if
    none exist it falls back to the first ``.gguf`` file alphabetically.
    Files smaller than :data:`MIN_MODEL_BYTES` are skipped.

    Parameters
    ----------
    models_dir:
        Directory to scan.  If it does not exist an empty list is
        returned.

    Returns
    -------
    list[ModelInfo]
        Sorted list (by model name) of discovered models.

    Raises
    ------
    TypeError
        If *models_dir* is not a :class:`~pathlib.Path`.
    ValueError
        If *models_dir* exists but is not a directory.
    """
    if not isinstance(models_dir, Path):
        raise TypeError(f"models_dir must be a Path, got {type(models_dir).__name__}")
    if not models_dir.exists():
        logger.debug("models_dir does not exist: %s", models_dir)
        return []
    if not models_dir.is_dir():
        raise ValueError(f"models_dir is not a directory: {models_dir}")

    found: list[ModelInfo] = []

    for model_dir in sorted(models_dir.iterdir()):
        if not model_dir.is_dir():
            continue

        candidates = sorted(model_dir.glob("*.gguf"))
        if not candidates:
            logger.debug("No .gguf files in %s — skipping", model_dir)
            continue

        preferred = [f for f in candidates if "i2_s" in f.name]
        chosen = preferred[0] if preferred else candidates[0]

        size = chosen.stat().st_size
        if size < MIN_MODEL_BYTES:
            logger.debug("Skipping %s — too small (%d bytes)", chosen.name, size)
            continue

        info = ModelInfo(name=model_dir.name, path=chosen, size_bytes=size)
        found.append(info)
        logger.debug("Discovered model: %s (%s)", info.name, _fmt_bytes(size))

    return found

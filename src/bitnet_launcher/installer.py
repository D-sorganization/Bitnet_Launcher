"""BitNet installation detection and guided setup utilities.

Provides :func:`check_installation` for inspecting an existing BitNet
checkout, :func:`install_bitnet` for cloning and pip-installing, and
:func:`build_bitnet` for running the cmake build.
"""

from __future__ import annotations

import importlib
import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

BITNET_REPO_URL: str = "https://github.com/microsoft/BitNet.git"


# ---------------------------------------------------------------------------
# Status dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InstallStatus:
    """Snapshot of a BitNet installation's health.

    Parameters
    ----------
    root_exists:
        ``True`` if *bitnet_root* exists as a directory.
    llama_cli_exists:
        ``True`` if ``build/bin/llama-cli`` exists inside *bitnet_root*.
    models_dir_exists:
        ``True`` if the ``models/`` directory exists inside *bitnet_root*.
    python_deps_ok:
        ``True`` if ``huggingface_hub`` is importable.
    setup_env_exists:
        ``True`` if ``setup_env.py`` exists inside *bitnet_root*.
    """

    root_exists: bool
    llama_cli_exists: bool
    models_dir_exists: bool
    python_deps_ok: bool
    setup_env_exists: bool

    @property
    def is_ready(self) -> bool:
        """``True`` if BitNet is fully installed and usable.

        Requires the ``llama-cli`` binary and at least a ``models/`` directory.
        """
        return self.llama_cli_exists and self.models_dir_exists

    @property
    def summary(self) -> str:
        """One-line human-readable installation status."""
        if self.is_ready:
            return "BitNet is installed and ready."
        if not self.root_exists:
            return "BitNet not found. Click Install to set up."
        if not self.llama_cli_exists:
            return "BitNet found but not built. Run the build step."
        return "BitNet partially installed."


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def check_installation(bitnet_root: Path) -> InstallStatus:
    """Inspect *bitnet_root* and return the current :class:`InstallStatus`.

    Parameters
    ----------
    bitnet_root:
        Directory to inspect.

    Returns
    -------
    InstallStatus
        Populated status object.

    Raises
    ------
    TypeError
        If *bitnet_root* is not a :class:`~pathlib.Path`.
    """
    if not isinstance(bitnet_root, Path):
        raise TypeError(f"bitnet_root must be a Path, got {type(bitnet_root).__name__}")

    root_exists = bitnet_root.is_dir()
    llama_cli_exists = (bitnet_root / "build" / "bin" / "llama-cli").exists()
    models_dir_exists = (bitnet_root / "models").is_dir()
    setup_env_exists = (bitnet_root / "setup_env.py").is_file()

    try:
        importlib.import_module("huggingface_hub")
        python_deps_ok = True
    except ImportError:
        python_deps_ok = False

    status = InstallStatus(
        root_exists=root_exists,
        llama_cli_exists=llama_cli_exists,
        models_dir_exists=models_dir_exists,
        python_deps_ok=python_deps_ok,
        setup_env_exists=setup_env_exists,
    )
    logger.debug("InstallStatus for %s: %s", bitnet_root, status)
    return status


def install_bitnet(
    install_path: Path,
    on_log: Callable[[str], None],
) -> None:
    """Clone the BitNet repo and install Python requirements.

    Runs (in sequence)::

        git clone https://github.com/microsoft/BitNet.git <install_path>
        pip install -r <install_path>/requirements.txt

    Each output line is streamed to *on_log*.

    Parameters
    ----------
    install_path:
        Target directory for the clone.  Must not already exist as a
        non-empty directory.
    on_log:
        Callback receiving each line of subprocess output.

    Raises
    ------
    TypeError
        If any argument has the wrong type.
    RuntimeError
        If ``git clone`` or ``pip install`` exits with a non-zero code.
    """
    if not isinstance(install_path, Path):
        raise TypeError(
            f"install_path must be a Path, got {type(install_path).__name__}"
        )
    if not callable(on_log):
        raise TypeError("on_log must be callable")

    logger.info("Cloning BitNet into %s", install_path)
    _run_streaming(
        ["git", "clone", BITNET_REPO_URL, str(install_path)],
        cwd=None,
        on_log=on_log,
        error_prefix="git clone failed",
    )

    req_file = install_path / "requirements.txt"
    if req_file.exists():
        logger.info("Installing requirements from %s", req_file)
        _run_streaming(
            ["pip", "install", "-r", str(req_file)],
            cwd=str(install_path),
            on_log=on_log,
            error_prefix="pip install failed",
        )
    else:
        on_log("requirements.txt not found — skipping pip install")
        logger.warning("requirements.txt not found at %s", req_file)


def build_bitnet(
    bitnet_root: Path,
    on_log: Callable[[str], None],
) -> None:
    """Run the cmake build inside *bitnet_root*.

    Runs::

        cmake -B build -DLLAMA_NATIVE=OFF
        cmake --build build --config Release -j

    Streams all output to *on_log*.

    Parameters
    ----------
    bitnet_root:
        Root of the BitNet checkout (must contain a ``CMakeLists.txt``).
    on_log:
        Callback receiving each line of subprocess output.

    Raises
    ------
    TypeError
        If any argument has the wrong type.
    ValueError
        If *bitnet_root* does not exist.
    RuntimeError
        If any cmake command exits with a non-zero return code.
    """
    if not isinstance(bitnet_root, Path):
        raise TypeError(f"bitnet_root must be a Path, got {type(bitnet_root).__name__}")
    if not callable(on_log):
        raise TypeError("on_log must be callable")
    if not bitnet_root.is_dir():
        raise ValueError(
            f"bitnet_root does not exist or is not a directory: {bitnet_root}"
        )

    cwd = str(bitnet_root)
    logger.info("Running cmake configure in %s", bitnet_root)
    _run_streaming(
        ["cmake", "-B", "build", "-DLLAMA_NATIVE=OFF"],
        cwd=cwd,
        on_log=on_log,
        error_prefix="cmake configure failed",
    )

    logger.info("Running cmake build in %s", bitnet_root)
    _run_streaming(
        ["cmake", "--build", "build", "--config", "Release", "-j"],
        cwd=cwd,
        on_log=on_log,
        error_prefix="cmake build failed",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_streaming(
    cmd: list[str],
    cwd: str | None,
    on_log: Callable[[str], None],
    error_prefix: str,
) -> None:
    """Run *cmd*, streaming merged stdout+stderr to *on_log*.

    Parameters
    ----------
    cmd:
        Command vector.
    cwd:
        Working directory, or ``None`` to use the caller's cwd.
    on_log:
        Line callback.
    error_prefix:
        Prefix for the :class:`RuntimeError` message on failure.

    Raises
    ------
    RuntimeError
        If the command exits with a non-zero return code.
    """
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
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
                    logger.debug("subprocess: %s", stripped)
        return_code = process.wait()
    except OSError as exc:
        raise RuntimeError(f"{error_prefix}: {exc}") from exc

    if return_code != 0:
        raise RuntimeError(f"{error_prefix} (exit code {return_code})")

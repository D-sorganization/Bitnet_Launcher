"""Behavioral tests for installer subprocess orchestration.

Covers the previously-untested streaming paths of
:func:`~bitnet_launcher.installer.install_bitnet`,
:func:`~bitnet_launcher.installer.build_bitnet`, and the shared
``_run_streaming`` helper: the merged stdout/stderr line pump, blank-line
filtering, non-zero exit -> ``RuntimeError``, ``OSError`` wrapping, the
``requirements.txt`` skip branch, and the partial-install summary.

All subprocess interaction is faked at the ``subprocess.Popen`` boundary, so
these tests never spawn a real ``git`` / ``pip`` / ``cmake`` process and run
fully offline and headless-safe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import bitnet_launcher.installer as installer
from bitnet_launcher.installer import (
    InstallStatus,
    build_bitnet,
    check_installation,
    install_bitnet,
)


class _FakePopen:
    """Minimal stand-in for ``subprocess.Popen`` with text-mode stdout.

    Records the command and cwd it was invoked with, yields *lines* from
    ``stdout``, and reports *returncode* from ``wait()``.
    """

    instances: list[_FakePopen] = []

    def __init__(
        self,
        cmd: list[str],
        cwd: str | None = None,
        stdout: object = None,
        stderr: object = None,
        text: bool = False,
        bufsize: int = -1,
    ) -> None:
        self.cmd = cmd
        self.cwd = cwd
        self._lines = list(self._scripted_lines)
        self.stdout = iter(self._lines)
        self._returncode = self._scripted_returncode
        _FakePopen.instances.append(self)

    # Per-test configuration (patched onto the class before use).
    _scripted_lines: list[str] = []
    _scripted_returncode: int = 0

    def wait(self) -> int:
        return self._returncode


@pytest.fixture()
def fake_popen(monkeypatch: pytest.MonkeyPatch):
    """Install a configurable fake Popen and return a configure() helper."""
    _FakePopen.instances = []

    def configure(lines: list[str], returncode: int = 0) -> type[_FakePopen]:
        _FakePopen._scripted_lines = lines
        _FakePopen._scripted_returncode = returncode
        return _FakePopen

    monkeypatch.setattr(installer.subprocess, "Popen", _FakePopen)
    return configure


# ---------------------------------------------------------------------------
# install_bitnet
# ---------------------------------------------------------------------------


def test_install_bitnet_clones_and_installs_requirements(
    fake_popen, tmp_path: Path
) -> None:
    """With a requirements.txt present, both git clone and pip install run."""
    install_path = tmp_path / "BitNet"
    install_path.mkdir()
    (install_path / "requirements.txt").write_text("huggingface_hub\n")
    fake_popen(["clone ok"], returncode=0)

    logs: list[str] = []
    install_bitnet(install_path, logs.append)

    assert len(_FakePopen.instances) == 2, "expected git clone + pip install"
    clone_cmd = _FakePopen.instances[0].cmd
    pip_cmd = _FakePopen.instances[1].cmd
    assert clone_cmd[:2] == ["git", "clone"]
    assert str(install_path) in clone_cmd
    assert pip_cmd[:3] == ["pip", "install", "-r"]
    assert "clone ok" in logs


def test_install_bitnet_skips_pip_when_no_requirements(
    fake_popen, tmp_path: Path
) -> None:
    """Missing requirements.txt -> only git clone runs and a notice is logged."""
    install_path = tmp_path / "BitNet"
    fake_popen(["cloning"], returncode=0)

    logs: list[str] = []
    install_bitnet(install_path, logs.append)

    assert len(_FakePopen.instances) == 1, "pip install must be skipped"
    assert any("requirements.txt not found" in line for line in logs)


def test_install_bitnet_raises_on_clone_failure(fake_popen, tmp_path: Path) -> None:
    """A non-zero git clone exit aborts before pip and raises RuntimeError."""
    install_path = tmp_path / "BitNet"
    (install_path).mkdir()
    (install_path / "requirements.txt").write_text("x\n")
    fake_popen(["fatal: bad"], returncode=128)

    with pytest.raises(RuntimeError, match="git clone failed"):
        install_bitnet(install_path, lambda _s: None)

    # Failure happens on the first command; pip must never be reached.
    assert len(_FakePopen.instances) == 1


def test_install_bitnet_type_error_on_callback() -> None:
    """A non-callable on_log is rejected before any subprocess starts."""
    with pytest.raises(TypeError, match="on_log must be callable"):
        install_bitnet(Path("x"), "not-callable")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# build_bitnet
# ---------------------------------------------------------------------------


def test_build_bitnet_runs_configure_then_build(fake_popen, tmp_path: Path) -> None:
    """build_bitnet issues cmake configure then cmake --build, in order."""
    fake_popen(["-- Build files written"], returncode=0)

    logs: list[str] = []
    build_bitnet(tmp_path, logs.append)

    assert len(_FakePopen.instances) == 2
    configure_cmd = _FakePopen.instances[0].cmd
    build_cmd = _FakePopen.instances[1].cmd
    assert configure_cmd == ["cmake", "-B", "build", "-DLLAMA_NATIVE=OFF"]
    assert build_cmd == ["cmake", "--build", "build", "--config", "Release", "-j"]
    # Both commands run inside the bitnet_root.
    assert _FakePopen.instances[0].cwd == str(tmp_path)
    assert _FakePopen.instances[1].cwd == str(tmp_path)


def test_build_bitnet_raises_on_configure_failure(fake_popen, tmp_path: Path) -> None:
    """A failing cmake configure aborts before the build step."""
    fake_popen(["CMake Error"], returncode=1)

    with pytest.raises(RuntimeError, match="cmake configure failed"):
        build_bitnet(tmp_path, lambda _s: None)

    assert len(_FakePopen.instances) == 1, (
        "build step must not run after configure fail"
    )


def test_build_bitnet_value_error_on_missing_root(tmp_path: Path) -> None:
    """build_bitnet rejects a non-existent root before spawning cmake."""
    missing = tmp_path / "nope"
    with pytest.raises(ValueError, match="does not exist"):
        build_bitnet(missing, lambda _s: None)


def test_build_bitnet_type_error_on_root() -> None:
    with pytest.raises(TypeError, match="bitnet_root must be a Path"):
        build_bitnet("not-a-path", lambda _s: None)  # type: ignore[arg-type]


def test_build_bitnet_type_error_on_callback(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="on_log must be callable"):
        build_bitnet(tmp_path, 123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _run_streaming line-pump semantics (via build_bitnet)
# ---------------------------------------------------------------------------


def test_run_streaming_filters_empty_lines_and_strips_newlines(
    fake_popen, tmp_path: Path
) -> None:
    """Empty lines are dropped and trailing newlines stripped.

    The pump filters on ``line.rstrip("\\n")`` being truthy, so a fully blank
    line (``"\\n"``) is dropped while a whitespace-only line (``"  \\n"``) is
    preserved as ``"  "`` — this test pins that exact contract.
    """
    fake_popen(["first\n", "\n", "  \n", "second\n"], returncode=0)

    logs: list[str] = []
    build_bitnet(tmp_path, logs.append)

    assert "first" in logs
    assert "second" in logs
    assert "" not in logs, "fully-empty lines must be filtered out"
    assert "  " in logs, "whitespace-only lines are intentionally preserved"


def test_run_streaming_wraps_oserror_as_runtimeerror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An OSError from Popen (e.g. cmake not on PATH) becomes a RuntimeError."""

    def boom(*_a: object, **_k: object) -> None:
        raise OSError("No such file or directory: 'cmake'")

    monkeypatch.setattr(installer.subprocess, "Popen", boom)

    with pytest.raises(RuntimeError, match="cmake configure failed"):
        build_bitnet(tmp_path, lambda _s: None)


# ---------------------------------------------------------------------------
# Partial-install summary branch (installer line 68)
# ---------------------------------------------------------------------------


def test_summary_partially_installed(tmp_path: Path) -> None:
    """root + binary present but no models dir -> 'partially installed'."""
    s = InstallStatus(
        root_exists=True,
        llama_cli_exists=True,
        models_dir_exists=False,
        python_deps_ok=True,
        setup_env_exists=True,
    )
    assert not s.is_ready
    assert "partially installed" in s.summary.lower()


def test_summary_found_but_not_built(tmp_path: Path) -> None:
    """root present, binary missing -> 'not built' guidance."""
    (tmp_path / "models").mkdir()  # models dir present, but no binary
    status = check_installation(tmp_path)
    assert status.root_exists
    assert not status.llama_cli_exists
    assert "not built" in status.summary.lower()

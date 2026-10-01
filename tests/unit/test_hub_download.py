"""Behavioral tests for hub download orchestration.

Covers the previously-untested bodies of
:func:`~bitnet_launcher.hub.download_model` (the ``setup_env.py`` subprocess
path) and :func:`~bitnet_launcher.hub._download_prebuilt_gguf` (HuggingFace
file resolution, the TQ2_0 fallback, and every error branch).

The ``setup_env.py`` subprocess is faked at the ``subprocess.Popen``
boundary; the HuggingFace helpers are injected via ``monkeypatch`` so no real
network access ever occurs.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import bitnet_launcher.hub as hub
from bitnet_launcher.hub import CATALOG, HubModel, download_model


def _plain_model() -> HubModel:
    """A catalog entry that uses setup_env.py (no prebuilt gguf_file)."""
    return next(m for m in CATALOG if m.gguf_file is None)


def _gguf_model() -> HubModel:
    """A catalog entry that is a prebuilt GGUF download."""
    return next(m for m in CATALOG if m.gguf_file is not None)


# ---------------------------------------------------------------------------
# download_model — setup_env.py subprocess path
# ---------------------------------------------------------------------------


class _FakePopen:
    instances: list[_FakePopen] = []
    _scripted_lines: list[str] = []
    _scripted_returncode: int = 0

    def __init__(self, cmd, cwd=None, stdout=None, stderr=None, text=False, bufsize=-1):
        self.cmd = cmd
        self.cwd = cwd
        self.stdout = iter(list(self._scripted_lines))
        self._returncode = self._scripted_returncode
        _FakePopen.instances.append(self)

    def wait(self) -> int:
        return self._returncode


@pytest.fixture()
def fake_popen(monkeypatch: pytest.MonkeyPatch):
    _FakePopen.instances = []

    def configure(lines: list[str], returncode: int = 0):
        _FakePopen._scripted_lines = lines
        _FakePopen._scripted_returncode = returncode

    monkeypatch.setattr(hub.subprocess, "Popen", _FakePopen)
    return configure


def test_download_model_missing_setup_env_raises(tmp_path: Path) -> None:
    """A bitnet_root without setup_env.py is rejected with ValueError."""
    model = _plain_model()
    with pytest.raises(ValueError, match="setup_env.py not found"):
        download_model(
            model, tmp_path / "models", tmp_path, lambda _s: None, lambda _f: None
        )


def test_download_model_success_streams_and_returns_dest(
    fake_popen, tmp_path: Path
) -> None:
    """Happy path: streams non-blank log lines, reports progress, returns dest."""
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()
    (bitnet_root / "setup_env.py").write_text("# stub\n")
    models_dir = tmp_path / "models"
    fake_popen(["fetching weights\n", "\n", "quantizing\n"], returncode=0)

    model = _plain_model()
    logs: list[str] = []
    progress: list[float] = []
    dest = download_model(model, models_dir, bitnet_root, logs.append, progress.append)

    assert dest == models_dir / model.name
    assert models_dir.is_dir(), "models_dir must be created"
    assert logs == ["fetching weights", "quantizing"]  # blank line filtered
    assert progress[0] == 0.0 and progress[-1] == 1.0
    # The setup_env.py invocation carries the catalog repo id and quant flag.
    cmd = _FakePopen.instances[0].cmd
    assert "--hf-repo" in cmd
    assert model.repo_id in cmd
    assert cmd[cmd.index("-q") + 1] == "i2_s"
    assert _FakePopen.instances[0].cwd == str(bitnet_root)


def test_download_model_nonzero_exit_raises(fake_popen, tmp_path: Path) -> None:
    """A non-zero setup_env.py exit code surfaces as RuntimeError."""
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()
    (bitnet_root / "setup_env.py").write_text("# stub\n")
    fake_popen(["boom\n"], returncode=3)

    with pytest.raises(RuntimeError, match="exited with code 3"):
        download_model(
            _plain_model(),
            tmp_path / "models",
            bitnet_root,
            lambda _s: None,
            lambda _f: None,
        )


def test_download_model_oserror_wrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An OSError launching python3 is wrapped in RuntimeError."""
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()
    (bitnet_root / "setup_env.py").write_text("# stub\n")

    def boom(*_a, **_k):
        raise OSError("python3 not found")

    monkeypatch.setattr(hub.subprocess, "Popen", boom)

    with pytest.raises(RuntimeError, match="Failed to start setup_env.py"):
        download_model(
            _plain_model(),
            tmp_path / "models",
            bitnet_root,
            lambda _s: None,
            lambda _f: None,
        )


# ---------------------------------------------------------------------------
# _download_prebuilt_gguf — HuggingFace resolution + fallback + errors
# ---------------------------------------------------------------------------


def _install_fake_hf(
    monkeypatch: pytest.MonkeyPatch,
    *,
    repo_files: list[str],
    download_returns: str | None = None,
    list_raises: Exception | None = None,
    download_raises: Exception | None = None,
) -> dict:
    """Inject a fake ``huggingface_hub`` module and record call args."""
    calls: dict = {}

    def fake_list_repo_files(repo_id: str):
        calls["list_repo_id"] = repo_id
        if list_raises is not None:
            raise list_raises
        return repo_files

    def fake_hf_hub_download(repo_id: str, filename: str, local_dir: str):
        calls["download"] = {
            "repo_id": repo_id,
            "filename": filename,
            "local_dir": local_dir,
        }
        if download_raises is not None:
            raise download_raises
        return download_returns or str(Path(local_dir) / filename)

    fake_mod = types.ModuleType("huggingface_hub")
    fake_mod.list_repo_files = fake_list_repo_files  # type: ignore[attr-defined]
    fake_mod.hf_hub_download = fake_hf_hub_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_mod)
    return calls


def test_prebuilt_gguf_exact_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When the exact gguf_file exists in the repo, it is downloaded as-is."""
    model = _gguf_model()
    calls = _install_fake_hf(
        monkeypatch,
        repo_files=[model.gguf_file, "README.md"],  # type: ignore[list-item]
    )
    models_dir = tmp_path / "models"

    progress: list[float] = []
    out = hub._download_prebuilt_gguf(
        model, models_dir, lambda _s: None, progress.append
    )

    assert calls["download"]["filename"] == model.gguf_file
    assert calls["download"]["repo_id"] == model.repo_id
    assert (models_dir / model.name).is_dir()
    assert progress[0] == 0.0 and progress[-1] == 1.0
    assert isinstance(out, Path)


def test_prebuilt_gguf_falls_back_to_tq2_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If the exact name is absent, the first *tq2_0* gguf is used instead."""
    model = _gguf_model()
    # Exact filename missing; a differently-cased TQ2_0 file is present.
    repo_files = ["model-TQ2_0.GGUF", "model-bf16.gguf", "config.json"]
    calls = _install_fake_hf(monkeypatch, repo_files=repo_files)

    logs: list[str] = []
    hub._download_prebuilt_gguf(
        model, tmp_path / "models", logs.append, lambda _f: None
    )

    assert calls["download"]["filename"] == "model-TQ2_0.GGUF"
    assert any("not found" in line for line in logs)


def test_prebuilt_gguf_no_ternary_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No TQ2_0 gguf anywhere -> RuntimeError listing available files."""
    model = _gguf_model()
    _install_fake_hf(monkeypatch, repo_files=["model-bf16.gguf", "README.md"])

    with pytest.raises(RuntimeError, match="No TQ2_0 .gguf found"):
        hub._download_prebuilt_gguf(
            model, tmp_path / "models", lambda _s: None, lambda _f: None
        )


def test_prebuilt_gguf_list_failure_wrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failure listing repo files is wrapped in RuntimeError."""
    model = _gguf_model()
    _install_fake_hf(monkeypatch, repo_files=[], list_raises=ConnectionError("dns"))

    with pytest.raises(RuntimeError, match="Failed to list files"):
        hub._download_prebuilt_gguf(
            model, tmp_path / "models", lambda _s: None, lambda _f: None
        )


def test_prebuilt_gguf_download_failure_wrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A download error is wrapped in RuntimeError naming the file."""
    model = _gguf_model()
    _install_fake_hf(
        monkeypatch,
        repo_files=[model.gguf_file],  # type: ignore[list-item]
        download_raises=OSError("disk full"),
    )

    with pytest.raises(RuntimeError, match="Failed to download"):
        hub._download_prebuilt_gguf(
            model, tmp_path / "models", lambda _s: None, lambda _f: None
        )


def test_prebuilt_gguf_missing_dependency_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If huggingface_hub cannot be imported, a clear RuntimeError is raised."""
    model = _gguf_model()
    # Force the in-function `from huggingface_hub import ...` to fail.
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)

    with pytest.raises(RuntimeError, match="huggingface_hub is required"):
        hub._download_prebuilt_gguf(
            model, tmp_path / "models", lambda _s: None, lambda _f: None
        )


def test_prebuilt_gguf_disables_xet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The Xet transfer workaround env var is set before downloading."""
    import os

    monkeypatch.delenv("HF_HUB_DISABLE_XET", raising=False)
    model = _gguf_model()
    _install_fake_hf(monkeypatch, repo_files=[model.gguf_file])  # type: ignore[list-item]

    hub._download_prebuilt_gguf(
        model, tmp_path / "models", lambda _s: None, lambda _f: None
    )

    assert os.environ.get("HF_HUB_DISABLE_XET") == "1"

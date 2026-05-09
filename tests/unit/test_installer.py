"""Tests for bitnet_launcher.installer — InstallStatus and DbC."""

from __future__ import annotations

from pathlib import Path

import pytest
from bitnet_launcher.installer import InstallStatus, check_installation, install_bitnet


def test_check_installation_empty_dir(tmp_path: Path) -> None:
    status = check_installation(tmp_path)
    # tmp_path exists as a directory, so root_exists is True
    assert status.root_exists
    assert not status.llama_cli_exists
    assert not status.is_ready


def test_check_installation_with_llama_cli(tmp_path: Path) -> None:
    bin_dir = tmp_path / "build" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "llama-cli").touch()
    (tmp_path / "models").mkdir()
    status = check_installation(tmp_path)
    assert status.llama_cli_exists
    assert status.models_dir_exists
    assert status.is_ready


def test_check_installation_type_error() -> None:
    with pytest.raises(TypeError):
        check_installation("/not/a/path")  # type: ignore[arg-type]


def test_install_status_summary_not_ready(tmp_path: Path) -> None:
    status = check_installation(tmp_path)
    assert isinstance(status.summary, str)
    assert len(status.summary) > 0


def test_install_status_is_ready_false() -> None:
    s = InstallStatus(
        root_exists=True,
        llama_cli_exists=False,
        models_dir_exists=True,
        python_deps_ok=True,
        setup_env_exists=True,
    )
    assert not s.is_ready


def test_install_status_is_ready_true() -> None:
    s = InstallStatus(
        root_exists=True,
        llama_cli_exists=True,
        models_dir_exists=True,
        python_deps_ok=True,
        setup_env_exists=True,
    )
    assert s.is_ready


def test_install_bitnet_type_error() -> None:
    with pytest.raises(TypeError):
        install_bitnet("/not/a/path", lambda x: None)  # type: ignore[arg-type]


def test_check_installation_nonexistent_dir(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    status = check_installation(missing)
    assert not status.root_exists
    assert not status.llama_cli_exists
    assert not status.models_dir_exists
    assert not status.is_ready
    assert "not found" in status.summary.lower()


def test_install_status_summary_ready() -> None:
    s = InstallStatus(
        root_exists=True,
        llama_cli_exists=True,
        models_dir_exists=True,
        python_deps_ok=True,
        setup_env_exists=True,
    )
    assert "ready" in s.summary.lower()


def test_install_status_summary_no_binary() -> None:
    s = InstallStatus(
        root_exists=True,
        llama_cli_exists=False,
        models_dir_exists=True,
        python_deps_ok=True,
        setup_env_exists=True,
    )
    assert not s.is_ready
    assert isinstance(s.summary, str)

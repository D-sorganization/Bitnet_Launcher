"""Unit tests for SetupDialog accessibility and selectable status labels."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel

import bitnet_launcher.gui.setup_dialog as setup_dialog_module
from bitnet_launcher.gui.setup_dialog import SetupDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _label_for(dialog, widget) -> QLabel:
    labels = [label for label in dialog.findChildren(QLabel) if label.buddy() is widget]
    assert len(labels) == 1
    return labels[0]


def test_setup_dialog_status_labels_selectable(qapp, tmp_path: Path) -> None:
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()

    dialog = SetupDialog(bitnet_root=bitnet_root)
    try:
        expected_flags = (
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        for lbl in (
            dialog._lbl_root,
            dialog._lbl_llama,
            dialog._lbl_models,
            dialog._lbl_deps,
            dialog._lbl_setup_env,
        ):
            assert lbl.textInteractionFlags() & expected_flags == expected_flags
    finally:
        dialog.close()


@pytest.mark.parametrize("outcome", ["success", "error"])
def test_setup_dialog_path_label_tooltip_follows_worker_state(
    qapp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()
    worker = SimpleNamespace(
        log_line=MagicMock(),
        finished=MagicMock(),
        error=MagicMock(),
        start=MagicMock(),
    )
    monkeypatch.setattr(
        setup_dialog_module, "InstallerWorker", lambda *args, **kwargs: worker
    )
    monkeypatch.setattr(setup_dialog_module.QMessageBox, "exec", lambda self: 0)

    dialog = SetupDialog(bitnet_root=bitnet_root)
    try:
        active_tip = "Absolute path to the BitNet installation directory"
        path_label = _label_for(dialog, dialog._path_edit)
        assert dialog._path_edit.isEnabled()
        assert dialog._path_edit.toolTip() == path_label.toolTip() == active_tip

        dialog._run_worker(setup_dialog_module._WorkerMode.BUILD)

        busy_tip = "An operation is currently in progress"
        assert not dialog._path_edit.isEnabled()
        assert dialog._path_edit.toolTip() == path_label.toolTip() == busy_tip

        if outcome == "success":
            dialog._on_worker_finished()
        else:
            dialog._on_worker_error("test failure")

        assert dialog._path_edit.isEnabled()
        assert dialog._path_edit.toolTip() == path_label.toolTip() == active_tip
    finally:
        dialog._worker = None
        dialog.close()

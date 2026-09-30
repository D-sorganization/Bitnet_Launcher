"""Unit tests for HubDialog accessibility and tooltips."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QApplication, QLabel

import bitnet_launcher.gui.hub_dialog as hub_dialog_module
from bitnet_launcher.gui.hub_dialog import HubDialog
from bitnet_launcher.hub import CATALOG


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


def test_hub_dialog_table_tooltip(qapp, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()

    dialog = HubDialog(models_dir=models_dir, bitnet_root=bitnet_root)
    try:
        assert dialog._table.toolTip() == "Double-click or press Enter to download"
        assert dialog._table.accessibleName() == "Available Models"
    finally:
        dialog.close()


@pytest.mark.parametrize("outcome", ["success", "error"])
def test_hub_dialog_filter_label_tooltips_follow_download_state(
    qapp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    bitnet_root = tmp_path / "bitnet"
    bitnet_root.mkdir()
    worker = SimpleNamespace(
        log_line=MagicMock(),
        progress=MagicMock(),
        finished=MagicMock(),
        error=MagicMock(),
        start=MagicMock(),
        isRunning=lambda: False,
    )
    monkeypatch.setattr(
        hub_dialog_module, "DownloadWorker", lambda *args, **kwargs: worker
    )
    monkeypatch.setattr(hub_dialog_module.QMessageBox, "exec", lambda self: 0)

    dialog = HubDialog(models_dir=models_dir, bitnet_root=bitnet_root)
    try:
        search_label = _label_for(dialog, dialog._search)
        filter_label = _label_for(dialog, dialog._tag_combo)
        active_filter_tip = "Filter the model list by specific capabilities or sizes"
        active_tips = ("Filter models by name", active_filter_tip)
        inputs = (dialog._search, dialog._tag_combo)
        labels = (search_label, filter_label)
        assert all(widget.isEnabled() for widget in inputs)
        assert tuple(widget.toolTip() for widget in inputs) == active_tips
        assert tuple(label.toolTip() for label in labels) == active_tips

        monkeypatch.setattr(dialog, "_selected_model", lambda: CATALOG[0])
        dialog._start_download()

        busy_tip = "An operation is currently in progress"
        assert all(not widget.isEnabled() for widget in inputs)
        assert tuple(widget.toolTip() for widget in inputs) == (busy_tip,) * 2
        assert tuple(label.toolTip() for label in labels) == (busy_tip,) * 2

        if outcome == "success":
            dialog._on_download_finished()
        else:
            dialog._on_download_error("test failure")

        assert all(widget.isEnabled() for widget in inputs)
        assert tuple(widget.toolTip() for widget in inputs) == active_tips
        assert tuple(label.toolTip() for label in labels) == active_tips
    finally:
        dialog._worker = None
        dialog.close()

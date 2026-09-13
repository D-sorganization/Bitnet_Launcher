"""Unit tests for HubDialog accessibility and tooltips."""

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from bitnet_launcher.gui.hub_dialog import HubDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


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

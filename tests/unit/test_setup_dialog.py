"""Unit tests for SetupDialog accessibility and selectable status labels."""

from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from bitnet_launcher.gui.setup_dialog import SetupDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


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

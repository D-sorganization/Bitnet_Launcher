"""Unit tests for ModelPanel list refresh after model downloads."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication

from bitnet_launcher.gui import launcher_window
from bitnet_launcher.gui.model_panel import ModelPanel
from bitnet_launcher.models import ModelInfo


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _model(tmp_path: Path, name: str) -> ModelInfo:
    return ModelInfo(name=name, path=tmp_path / f"{name}.gguf", size_bytes=2048)


def _item_texts(panel: ModelPanel) -> list[str]:
    return [panel._list.item(i).text() for i in range(panel._list.count())]


def test_set_models_replaces_empty_state_with_new_models(qapp, tmp_path) -> None:
    panel = ModelPanel([])
    new = [_model(tmp_path, "alpha"), _model(tmp_path, "beta")]

    panel.set_models(new)

    assert _item_texts(panel) == [m.display_name for m in new]
    assert panel.selected_model == new[0]
    assert "alpha.gguf" in panel._detail.text()
    assert panel._list.toolTip() == "Double-click or press Enter to load model"


def test_set_models_empty_shows_placeholder_and_clears_detail(qapp, tmp_path) -> None:
    panel = ModelPanel([_model(tmp_path, "alpha")])

    panel.set_models([])

    assert _item_texts(panel) == [
        "No models found.\nUse 'Download Models' to get started."
    ]
    assert panel.selected_model is None
    assert panel._detail.text() == ""
    assert panel._list.toolTip() == ""


def test_set_models_rejects_non_list(qapp) -> None:
    panel = ModelPanel([])

    with pytest.raises(TypeError, match="models must be a list"):
        panel.set_models(("not", "a", "list"))  # type: ignore[arg-type]


def test_open_hub_dialog_pushes_refreshed_models_to_panel(
    qapp, tmp_path, monkeypatch
) -> None:
    downloaded = [_model(tmp_path, "fresh")]
    monkeypatch.setattr(
        launcher_window,
        "HubDialog",
        lambda **_kwargs: SimpleNamespace(exec=lambda: 0),
    )
    monkeypatch.setattr(launcher_window, "discover_models", lambda _d: downloaded)
    panel = ModelPanel([])
    window = SimpleNamespace(
        _cfg=SimpleNamespace(models_dir=tmp_path, bitnet_root=tmp_path),
        _models=[],
        _model_panel=panel,
    )

    launcher_window.BitNetLauncher._open_hub_dialog(window)  # type: ignore[arg-type]

    assert window._models == downloaded
    assert panel.selected_model == downloaded[0]

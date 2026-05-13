"""Model selection panel widget.

:class:`ModelPanel` displays a scrollable list of discovered models and a
detail label.  It exposes a ``selected_model`` property and emits the
``model_changed`` signal when the selection changes.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.models import ModelInfo, _fmt_bytes
from bitnet_launcher.theme import CatppuccinTheme

logger = logging.getLogger(__name__)


class ModelPanel(QWidget):
    """Widget that lists available models and shows selection details.

    Signals
    -------
    model_changed(ModelInfo):
        Emitted when the user selects a different model.
    """

    model_changed = pyqtSignal(object)  # carries ModelInfo

    def __init__(
        self,
        models: list[ModelInfo],
        parent: QWidget | None = None,
    ) -> None:
        """Initialise the panel.

        Parameters
        ----------
        models:
            Pre-discovered list of models to display.
        parent:
            Optional Qt parent widget.
        """
        if not isinstance(models, list):
            raise TypeError(f"models must be a list, got {type(models).__name__}")
        super().__init__(parent)

        self._models = models
        self._build_ui()

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def selected_model(self) -> ModelInfo | None:
        """Return the currently selected ModelInfo, or ``None``."""
        row = self._list.currentRow()
        if row < 0 or row >= len(self._models):
            return None
        return self._models[row]

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme
        group = QGroupBox("Models")
        group.setMinimumWidth(280)
        group_layout = QVBoxLayout(group)

        self._list = QListWidget()
        self._list.setAccessibleName("Model list")
        self._list.setFont(QFont("Consolas", 10))
        self._list.currentRowChanged.connect(self._on_row_changed)

        # ⚡ Bolt Optimization: Suspend list updates during batch insertions
        # Why: Prevents expensive synchronous layout recalculations and repaints
        # for every single cell inserted, drastically improving rendering speed
        # when dealing with a large number of models.
        self._list.setUpdatesEnabled(False)
        try:
            if self._models:
                for info in self._models:
                    item = QListWidgetItem(info.display_name)
                    item.setData(256, info)  # Qt.ItemDataRole.UserRole == 256
                    self._list.addItem(item)
                self._list.setCurrentRow(0)
            else:
                from PyQt6.QtGui import QColor

                empty_item = QListWidgetItem(
                    "No models found.\nUse 'Download Models' to get started."
                )
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_item.setForeground(QColor(t.SUBTEXT))
                self._list.addItem(empty_item)
        finally:
            self._list.setUpdatesEnabled(True)

        group_layout.addWidget(self._list)

        self._detail = QLabel()
        self._detail.setTextFormat(Qt.TextFormat.PlainText)
        self._detail.setWordWrap(True)
        self._detail.setStyleSheet(f"color: {t.SUBTEXT}; font-size: 10px;")
        group_layout.addWidget(self._detail)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

        if self._models:
            self._update_detail(self._models[0])

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._models):
            return
        info = self._models[row]
        self._update_detail(info)
        self.model_changed.emit(info)
        logger.debug("Model selected: %s", info.name)

    def _update_detail(self, info: ModelInfo) -> None:
        self._detail.setText(
            f"File: {info.path.name}\n"
            f"Size: {_fmt_bytes(info.size_bytes)}\n"
            f"Path: {info.path}"
        )

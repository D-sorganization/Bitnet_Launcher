"""Inference settings panel widget.

SettingsPanel provides spinboxes for threads, context size, temperature,
and max tokens, plus a system-prompt text area.  The ``inference_config``
property returns a validated InferenceConfig.
"""

from __future__ import annotations

import logging
import os

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.config import InferenceConfig

logger = logging.getLogger(__name__)


def _labeled_row(label: str, widget: QWidget) -> QHBoxLayout:
    """Return a horizontal layout with a fixed-width label and *widget*."""
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(120)
    lbl.setBuddy(widget)
    if widget.toolTip():
        lbl.setToolTip(widget.toolTip())
    row.addWidget(lbl)
    row.addWidget(widget)
    return row


class SettingsPanel(QWidget):
    """Widget that exposes inference hyperparameter controls.

    Parameters
    ----------
    parent:
        Optional Qt parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def inference_config(self) -> InferenceConfig:
        """Read current control values and return a validated InferenceConfig."""
        system = self._system_prompt.toPlainText().strip()
        if not system:
            system = "You are a helpful assistant."
        return InferenceConfig(
            threads=self._threads.value(),
            ctx_size=self._ctx_size.value(),
            temperature=self._temperature.value(),
            n_predict=self._n_predict.value(),
            system_prompt=system,
        )

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        group = QGroupBox("Settings")
        layout = QVBoxLayout(group)

        self._threads = QSpinBox()
        self._threads.setAccessibleName("Threads")
        self._threads.setRange(1, os.cpu_count() or 8)
        self._threads.setValue(min(4, os.cpu_count() or 4))
        self._threads.setSuffix(" threads")
        self._threads.setToolTip("CPU threads for inference")
        layout.addLayout(_labeled_row("&Threads:", self._threads))

        self._ctx_size = QSpinBox()
        self._ctx_size.setAccessibleName("Context size")
        self._ctx_size.setRange(512, 32768)
        self._ctx_size.setSingleStep(512)
        self._ctx_size.setValue(2048)
        self._ctx_size.setSuffix(" tokens")
        self._ctx_size.setToolTip("Context window size (tokens)")
        layout.addLayout(_labeled_row("&Context size:", self._ctx_size))

        self._temperature = QDoubleSpinBox()
        self._temperature.setAccessibleName("Temperature")
        self._temperature.setRange(0.0, 2.0)
        self._temperature.setSingleStep(0.05)
        self._temperature.setValue(0.8)
        self._temperature.setDecimals(2)
        self._temperature.setToolTip("Sampling temperature (0 = deterministic)")
        layout.addLayout(_labeled_row("T&emperature:", self._temperature))

        self._n_predict = QSpinBox()
        self._n_predict.setAccessibleName("Max tokens")
        self._n_predict.setRange(-1, 8192)
        self._n_predict.setValue(-1)
        self._n_predict.setSuffix(" tokens")
        self._n_predict.setSpecialValueText("unlimited")
        self._n_predict.setToolTip(
            "Max tokens to generate per response (-1 = unlimited)"
        )
        layout.addLayout(_labeled_row("&Max tokens:", self._n_predict))

        from bitnet_launcher.gui.wheel_event_filter import suppress_wheel_on_widgets

        suppress_wheel_on_widgets(
            [self._threads, self._ctx_size, self._temperature, self._n_predict]
        )

        layout.addSpacing(6)
        lbl_system_prompt = QLabel("&System prompt:")
        tooltip_text = (
            "Base instructions that define the AI's persona and overall behavior"
        )
        lbl_system_prompt.setToolTip(tooltip_text)
        layout.addWidget(lbl_system_prompt)

        self._system_prompt = QTextEdit()
        self._system_prompt.setAcceptRichText(False)
        lbl_system_prompt.setBuddy(self._system_prompt)
        self._system_prompt.setAccessibleName("System prompt")
        self._system_prompt.setPlaceholderText("You are a helpful assistant.")
        self._system_prompt.setToolTip(tooltip_text)
        self._system_prompt.setTabChangesFocus(True)
        self._system_prompt.setFixedHeight(80)
        self._system_prompt.setFont(QFont("Consolas", 10))
        layout.addWidget(self._system_prompt)
        layout.addStretch()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

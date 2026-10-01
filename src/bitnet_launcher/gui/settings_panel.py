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


def _labeled_row(label: str, widget: QWidget) -> tuple[QHBoxLayout, QLabel]:
    """Return a horizontal layout with a fixed-width label and *widget*."""
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(120)
    lbl.setBuddy(widget)
    if widget.toolTip():
        lbl.setToolTip(widget.toolTip())
    row.addWidget(lbl)
    row.addWidget(widget)
    return row, lbl


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

    def setEnabled(self, enabled: bool) -> None:
        """Update tooltips for inputs and labels when disabled/enabled."""
        super().setEnabled(enabled)
        if enabled:
            self._threads.setToolTip("CPU threads for inference")
            self._lbl_threads.setToolTip("CPU threads for inference")
            self._ctx_size.setToolTip("Context window size (tokens)")
            self._lbl_ctx_size.setToolTip("Context window size (tokens)")
            self._temperature.setToolTip("Sampling temperature (0 = deterministic)")
            self._lbl_temperature.setToolTip("Sampling temperature (0 = deterministic)")
            self._n_predict.setToolTip(
                "Max tokens to generate per response (-1 = unlimited)"
            )
            self._lbl_n_predict.setToolTip(
                "Max tokens to generate per response (-1 = unlimited)"
            )
            sys_tooltip = (
                "Base instructions that define the AI's persona and overall behavior"
            )
            self._system_prompt.setToolTip(sys_tooltip)
            self._lbl_system_prompt.setToolTip(sys_tooltip)
        else:
            msg = "Stop the active chat session to modify inference settings"
            self._threads.setToolTip(msg)
            self._lbl_threads.setToolTip(msg)
            self._ctx_size.setToolTip(msg)
            self._lbl_ctx_size.setToolTip(msg)
            self._temperature.setToolTip(msg)
            self._lbl_temperature.setToolTip(msg)
            self._n_predict.setToolTip(msg)
            self._lbl_n_predict.setToolTip(msg)
            self._system_prompt.setToolTip(msg)
            self._lbl_system_prompt.setToolTip(msg)

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
        row, self._lbl_threads = _labeled_row("&Threads:", self._threads)
        layout.addLayout(row)

        self._ctx_size = QSpinBox()
        self._ctx_size.setAccessibleName("Context size")
        self._ctx_size.setRange(512, 32768)
        self._ctx_size.setSingleStep(512)
        self._ctx_size.setValue(2048)
        self._ctx_size.setSuffix(" tokens")
        self._ctx_size.setToolTip("Context window size (tokens)")
        row, self._lbl_ctx_size = _labeled_row("&Context size:", self._ctx_size)
        layout.addLayout(row)

        self._temperature = QDoubleSpinBox()
        self._temperature.setAccessibleName("Temperature")
        self._temperature.setRange(0.0, 2.0)
        self._temperature.setSingleStep(0.05)
        self._temperature.setValue(0.8)
        self._temperature.setDecimals(2)
        self._temperature.setToolTip("Sampling temperature (0 = deterministic)")
        row, self._lbl_temperature = _labeled_row("T&emperature:", self._temperature)
        layout.addLayout(row)

        self._n_predict = QSpinBox()
        self._n_predict.setAccessibleName("Max tokens")
        self._n_predict.setRange(-1, 8192)
        self._n_predict.setValue(-1)
        self._n_predict.setSuffix(" tokens")
        self._n_predict.setSpecialValueText("unlimited")
        self._n_predict.setToolTip(
            "Max tokens to generate per response (-1 = unlimited)"
        )
        row, self._lbl_n_predict = _labeled_row("&Max tokens:", self._n_predict)
        layout.addLayout(row)

        from bitnet_launcher.gui.wheel_event_filter import suppress_wheel_on_widgets

        suppress_wheel_on_widgets(
            [self._threads, self._ctx_size, self._temperature, self._n_predict]
        )

        layout.addSpacing(6)
        self._lbl_system_prompt = QLabel("&System prompt:")
        tooltip_text = (
            "Base instructions that define the AI's persona and overall behavior"
        )
        self._lbl_system_prompt.setToolTip(tooltip_text)
        layout.addWidget(self._lbl_system_prompt)

        self._system_prompt = QTextEdit()
        # Security: Prevent HTML injection/UI redressing from pasted prompts
        self._system_prompt.setAcceptRichText(False)
        self._lbl_system_prompt.setBuddy(self._system_prompt)
        self._system_prompt.setAccessibleName("System prompt")
        self._system_prompt.setAcceptRichText(False)
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

"""Catppuccin Mocha colour theme for BitNet Launcher.

Provides colour constants as class attributes on :class:`CatppuccinTheme`
and two helper functions, :func:`build_palette` and :func:`build_stylesheet`,
for applying the theme to a :class:`~PyQt6.QtWidgets.QApplication`.
"""

from __future__ import annotations

import logging

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class CatppuccinTheme:
    """Catppuccin Mocha colour palette constants."""

    BG: str = "#1e1e2e"
    SURFACE: str = "#313244"
    OVERLAY: str = "#45475a"
    ACCENT: str = "#cba6f7"  # Mauve
    GREEN: str = "#a6e3a1"
    YELLOW: str = "#f9e2af"
    RED: str = "#f38ba8"
    TEXT: str = "#cdd6f4"
    SUBTEXT: str = "#a6adc8"


def build_palette(app: QApplication) -> None:
    """Apply the Catppuccin Mocha :class:`~PyQt6.QtGui.QPalette` to *app*.

    Parameters
    ----------
    app:
        The running :class:`~PyQt6.QtWidgets.QApplication` instance.

    Raises
    ------
    TypeError
        If *app* is not a :class:`~PyQt6.QtWidgets.QApplication`.
    """
    if not isinstance(app, QApplication):
        raise TypeError(f"app must be a QApplication, got {type(app).__name__}")

    t = CatppuccinTheme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t.BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t.TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(t.SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t.BG))
    palette.setColor(QPalette.ColorRole.Text, QColor(t.TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(t.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t.TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t.BG))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t.SUBTEXT))
    app.setPalette(palette)
    logger.debug("Catppuccin palette applied")


def build_stylesheet() -> str:
    """Return the global Qt stylesheet string for Catppuccin Mocha.

    Returns
    -------
    str
        A CSS-like Qt stylesheet ready to pass to
        :meth:`~PyQt6.QtWidgets.QWidget.setStyleSheet`.
    """
    t = CatppuccinTheme
    return f"""
        QMainWindow, QWidget {{
            background: {t.BG};
            color: {t.TEXT};
        }}
        QGroupBox {{
            border: 1px solid {t.SURFACE};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 4px;
            color: {t.SUBTEXT};
            font-size: 11px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
        }}
        QPushButton {{
            background: {t.SURFACE};
            color: {t.TEXT};
            border: 1px solid {t.OVERLAY};
            border-radius: 4px;
            padding: 4px 12px;
        }}
        QPushButton:hover {{
            background: {t.OVERLAY};
        }}
        QPushButton:disabled {{
            color: #585b70;
            border-color: {t.OVERLAY};
        }}
        QPushButton:focus {{
            border: 1px solid {t.ACCENT};
            outline: none;
        }}
        QListWidget {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 4px;
        }}
        QListWidget:focus {{
            border: 1px solid {t.ACCENT};
            outline: none;
        }}
        QListWidget::item:selected {{
            background: {t.ACCENT};
            color: {t.BG};
        }}
        QListWidget::item:hover {{
            background: {t.OVERLAY};
        }}
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 3px;
            color: {t.TEXT};
            padding: 2px 4px;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {t.ACCENT};
            outline: none;
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background: {t.OVERLAY};
        }}
    """

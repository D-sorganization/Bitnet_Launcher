"""Style sheets for Bitnet Launcher GUI components."""

from __future__ import annotations

from bitnet_launcher.theme import CatppuccinTheme


def get_hub_dialog_stylesheet() -> str:
    """Return a stylesheet suitable for the hub dialog."""
    t = CatppuccinTheme
    return f"""
        QDialog, QWidget {{
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
        QTableWidget {{
            background: {t.SURFACE};
            alternate-background-color: {t.BG};
            border: 1px solid {t.OVERLAY};
            gridline-color: {t.OVERLAY};
        }}
        QTableWidget::item:selected {{
            background: {t.ACCENT};
            color: {t.BG};
        }}
        QHeaderView::section {{
            background: {t.OVERLAY};
            color: {t.TEXT};
            padding: 4px;
            border: none;
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
        }}
        QPushButton:focus {{
            border: 1px solid {t.ACCENT};
            outline: none;
        }}
        QLineEdit, QComboBox {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 3px;
            color: {t.TEXT};
            padding: 2px 4px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {t.ACCENT};
        }}
        QTableWidget:focus {{
            border: 1px solid {t.ACCENT};
        }}
        QProgressBar {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 3px;
            text-align: center;
            color: {t.TEXT};
        }}
        QProgressBar::chunk {{
            background: {t.ACCENT};
            border-radius: 3px;
        }}
    """

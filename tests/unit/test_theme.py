import pytest
from PyQt6.QtGui import QPalette

from bitnet_launcher.theme import CatppuccinTheme, build_palette, build_stylesheet


def test_catppuccin_theme_constants():
    """Verify theme constants are defined correctly."""
    assert CatppuccinTheme.BG == "#1e1e2e"
    assert CatppuccinTheme.TEXT == "#cdd6f4"


def test_build_palette(qapp):
    """Test palette is applied correctly."""
    build_palette(qapp)
    palette = qapp.palette()
    assert isinstance(palette, QPalette)


def test_build_palette_invalid_type():
    """Verify TypeError raised if app is not QApplication."""
    with pytest.raises(TypeError, match="app must be a QApplication"):
        build_palette(object())


def test_build_stylesheet():
    """Test stylesheet string generation."""
    css = build_stylesheet()
    assert isinstance(css, str)
    assert CatppuccinTheme.BG in css
    assert "QMainWindow" in css

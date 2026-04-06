"""Entry point for BitNet Launcher.

Invoke as::

    python3 -m bitnet_launcher.app
    # or, if installed:
    bitnet-launcher
"""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from bitnet_launcher.gui.launcher_window import BitNetLauncher
from bitnet_launcher.theme import build_palette

logger = logging.getLogger(__name__)


def main() -> None:
    """Create the QApplication, apply the theme, and show the main window."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BitNet Launcher")

    build_palette(app)

    window = BitNetLauncher()
    window.show()

    logger.info("BitNet Launcher started")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

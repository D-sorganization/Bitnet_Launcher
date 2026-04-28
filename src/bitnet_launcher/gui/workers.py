"""Background workers for Bitnet Launcher GUI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

from bitnet_launcher.hub import download_model

if TYPE_CHECKING:
    from pathlib import Path

    from PyQt6.QtWidgets import QWidget

    from bitnet_launcher.hub import HubModel

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """Worker thread that runs :func:`~bitnet_launcher.hub.download_model`.

    Signals
    -------
    log_line(str):
        Emitted for each line of subprocess output.
    progress(float):
        Emitted with a value in ``[0.0, 1.0]``.
    finished():
        Emitted on successful completion.
    error(str):
        Emitted with a description if the download fails.
    """

    log_line = pyqtSignal(str)
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        hub_model: HubModel,
        models_dir: Path,
        bitnet_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise the worker.

        Parameters
        ----------
        hub_model:
            Model to download.
        models_dir:
            Directory where downloaded models are stored.
        bitnet_root:
            Root of the BitNet checkout containing ``setup_env.py``.
        parent:
            Optional Qt parent.
        """
        super().__init__(parent)
        self._hub_model = hub_model
        self._models_dir = models_dir
        self._bitnet_root = bitnet_root

    def run(self) -> None:
        """Execute the download in the worker thread."""
        try:
            download_model(
                self._hub_model,
                self._models_dir,
                self._bitnet_root,
                on_log=self.log_line.emit,
                on_progress=self.progress.emit,
            )
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("DownloadWorker error: %s", exc)
            self.error.emit(str(exc))

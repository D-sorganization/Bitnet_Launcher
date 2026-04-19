"""Model download dialog for BitNet Launcher.

:class:`HubDialog` lets the user browse the HuggingFace model catalog,
see installation status of each model, and trigger a download+quantize
operation via :func:`~bitnet_launcher.hub.download_model`.

The download runs in a :class:`DownloadWorker` ``QThread`` so the GUI
remains responsive.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.hub import CATALOG, HubModel, download_model
from bitnet_launcher.theme import CatppuccinTheme

logger = logging.getLogger(__name__)

_ALL_TAGS_LABEL = "All"


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------


class HubDialog(QDialog):
    """Dialog for browsing and downloading BitNet-compatible HuggingFace models.

    Parameters
    ----------
    models_dir:
        Directory where downloaded models are (or will be) stored.
    bitnet_root:
        Root of the BitNet checkout.
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        models_dir: Path,
        bitnet_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        if not isinstance(models_dir, Path):
            raise TypeError(
                f"models_dir must be a Path, got {type(models_dir).__name__}"
            )
        if not isinstance(bitnet_root, Path):
            raise TypeError(
                f"bitnet_root must be a Path, got {type(bitnet_root).__name__}"
            )
        super().__init__(parent)
        self._models_dir = models_dir
        self._bitnet_root = bitnet_root
        self._worker: DownloadWorker | None = None

        self.setWindowTitle("Download BitNet Models")
        self.resize(820, 640)
        self.setStyleSheet(_dialog_stylesheet())
        self._build_ui()
        self._populate_tag_filter()
        self._refresh_table()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))

        self._tag_combo = QComboBox()
        self._tag_combo.setFixedWidth(140)
        self._tag_combo.currentIndexChanged.connect(self._refresh_table)
        filter_row.addWidget(self._tag_combo)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name…")
        self._search.textChanged.connect(self._refresh_table)
        filter_row.addWidget(self._search)

        root.addLayout(filter_row)

        # Model table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Params", "Size (GB)", "Tags", "Status"]
        )
        header = self._table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        v_header = self._table.verticalHeader()
        assert v_header is not None
        v_header.setVisible(False)
        sel_model = self._table.selectionModel()
        assert sel_model is not None
        sel_model.selectionChanged.connect(self._on_selection_changed)
        root.addWidget(self._table)

        # Detail label
        self._detail_label = QLabel()
        self._detail_label.setWordWrap(True)
        self._detail_label.setStyleSheet(
            f"color: {t.SUBTEXT}; font-size: 11px; padding: 4px;"
        )
        root.addWidget(self._detail_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {t.OVERLAY};")
        root.addWidget(sep)

        # Log group
        log_group = QGroupBox("Output")
        log_layout = QVBoxLayout(log_group)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            f"background: {t.BG}; color: {t.TEXT}; border: 1px solid {t.SURFACE};"
        )
        log_layout.addWidget(self._log)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        log_layout.addWidget(self._progress)

        root.addWidget(log_group)

        # Button row
        btn_row = QHBoxLayout()
        self._btn_close = QPushButton("Close")
        self._btn_close.setFixedHeight(32)
        self._btn_close.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_close)

        btn_row.addStretch()

        self._btn_download = QPushButton("⬇  Download Selected")
        self._btn_download.setFixedHeight(32)
        self._btn_download.setEnabled(False)
        self._btn_download.setStyleSheet(
            f"QPushButton {{ color: {t.GREEN}; border-color: {t.GREEN}; }}"
            f"QPushButton:hover {{ background: #1e3a2f; }}"
            f"QPushButton:disabled {{ color: #585b70; }}"
        )
        self._btn_download.clicked.connect(self._start_download)
        btn_row.addWidget(self._btn_download)

        root.addLayout(btn_row)

    # ── Filter helpers ───────────────────────────────────────────────────────

    def _populate_tag_filter(self) -> None:
        """Fill the tag combo box with unique tags from CATALOG."""
        all_tags: set[str] = set()
        for model in CATALOG:
            all_tags.update(model.tags)
        self._tag_combo.addItem(_ALL_TAGS_LABEL)
        for tag in sorted(all_tags):
            self._tag_combo.addItem(tag)

    def _filtered_models(self) -> list[HubModel]:
        """Return models matching the current tag filter and search text."""
        tag = self._tag_combo.currentText()
        query = self._search.text().strip().lower()
        result: list[HubModel] = []
        for model in CATALOG:
            if tag != _ALL_TAGS_LABEL and tag not in model.tags:
                continue
            if query and query not in model.name.lower():
                continue
            result.append(model)
        return result

    def _is_installed(self, model: HubModel) -> bool:
        """Return ``True`` if the model's GGUF file already exists."""
        gguf = self._models_dir / model.name / "ggml-model-i2_s.gguf"
        return gguf.exists()

    # ── Table population ─────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        """Repopulate the table according to current filter settings."""
        t = CatppuccinTheme
        self._visible_models = self._filtered_models()
        self._table.setRowCount(len(self._visible_models))

        for row, model in enumerate(self._visible_models):
            installed = self._is_installed(model)

            name_item = QTableWidgetItem(model.name)
            name_item.setFont(QFont("Consolas", 9))
            self._table.setItem(row, 0, name_item)

            self._table.setItem(row, 1, QTableWidgetItem(model.params))
            self._table.setItem(row, 2, QTableWidgetItem(f"{model.size_gb:.1f}"))
            self._table.setItem(row, 3, QTableWidgetItem(", ".join(model.tags)))

            status_item = QTableWidgetItem("Installed" if installed else "—")
            if installed:
                status_item.setForeground(QColor(t.GREEN))
            else:
                status_item.setForeground(QColor(t.SUBTEXT))
            self._table.setItem(row, 4, status_item)

        self._btn_download.setEnabled(False)
        self._detail_label.setText("")

    def _on_selection_changed(self) -> None:
        """Update the detail label and download button when selection changes."""
        sel_model = self._table.selectionModel()
        assert sel_model is not None
        rows = sel_model.selectedRows()
        if not rows:
            self._btn_download.setEnabled(False)
            self._detail_label.setText("")
            return
        row = rows[0].row()
        if row >= len(self._visible_models):
            return
        model = self._visible_models[row]
        installed = self._is_installed(model)
        self._detail_label.setText(
            f"<b>{model.name}</b> — {model.params} params, "
            f"{model.size_gb:.1f} GB download<br>"
            f"{model.description}<br>"
            f"<i>HF repo: {model.repo_id}</i>"
        )
        self._btn_download.setEnabled(not installed and self._worker is None)

    # ── Download ─────────────────────────────────────────────────────────────

    def _selected_model(self) -> HubModel | None:
        """Return the currently selected :class:`~bitnet_launcher.hub.HubModel`."""
        sel_model = self._table.selectionModel()
        assert sel_model is not None
        rows = sel_model.selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        if row >= len(self._visible_models):
            return None
        return self._visible_models[row]

    def _start_download(self) -> None:
        """Start a :class:`DownloadWorker` for the selected model."""
        model = self._selected_model()
        if model is None:
            return

        setup_env = self._bitnet_root / "setup_env.py"
        if not setup_env.exists():
            QMessageBox.critical(
                self,
                "BitNet not found",
                f"setup_env.py not found at:\n{self._bitnet_root}\n\n"
                "Use the Setup dialog to install BitNet first.",
            )
            return

        self._log.clear()
        self._progress.setValue(0)
        self._btn_download.setEnabled(False)
        self._btn_close.setEnabled(False)
        self._append_log(f"Starting download: {model.name} …")

        self._worker = DownloadWorker(
            model, self._models_dir, self._bitnet_root, parent=self
        )
        self._worker.log_line.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.error.connect(self._on_download_error)
        self._worker.start()
        logger.info("Download started for %s", model.name)

    def _append_log(self, line: str) -> None:
        """Append *line* to the log text area."""
        self._log.append(line)

    def _on_progress(self, value: float) -> None:
        """Update the progress bar (0.0–1.0)."""
        self._progress.setValue(int(value * 100))

    def _on_download_finished(self) -> None:
        """Handle successful download completion."""
        self._progress.setValue(100)
        self._append_log("Download complete.")
        self._worker = None
        self._btn_close.setEnabled(True)
        self._refresh_table()
        logger.info("Download worker finished successfully")

    def _on_download_error(self, message: str) -> None:
        """Handle download failure."""
        self._append_log(f"ERROR: {message}")
        self._worker = None
        self._btn_download.setEnabled(True)
        self._btn_close.setEnabled(True)
        QMessageBox.critical(self, "Download Failed", message)
        logger.error("Download worker error: %s", message)

    def reject(self) -> None:
        """Block closing while a download is in progress."""
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(
                self, "Download in Progress", "Please wait for the download to finish."
            )
            return
        super().reject()


# ---------------------------------------------------------------------------
# Stylesheet helper
# ---------------------------------------------------------------------------


def _dialog_stylesheet() -> str:
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
        QLineEdit, QComboBox {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 3px;
            color: {t.TEXT};
            padding: 2px 4px;
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

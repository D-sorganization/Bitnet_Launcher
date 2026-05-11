"""Model download dialog for BitNet Launcher.

:class:`HubDialog` lets the user browse the HuggingFace model catalog,
see installation status of each model, and trigger a download+quantize
operation via :func:`~bitnet_launcher.hub.download_model`.

The download runs in a :class:`DownloadWorker` ``QThread`` so the GUI
remains responsive.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
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

from bitnet_launcher.gui.styles import get_hub_dialog_stylesheet
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
        # ⚡ Bolt Optimization: Cache synchronous disk I/O in UI loops
        self._installed_cache: dict[str, bool] = {}

        # ⚡ Bolt Optimization: Cache Qt objects to prevent instantiating them often
        t = CatppuccinTheme
        self._font_consolas_9 = QFont("Consolas", 9)
        self._color_green = QColor(t.GREEN)
        self._color_subtext = QColor(t.SUBTEXT)

        self.setWindowTitle("Download BitNet Models")
        self.resize(820, 640)
        self.setStyleSheet(get_hub_dialog_stylesheet())
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
        lbl_filter = QLabel("Filter:")
        filter_row.addWidget(lbl_filter)

        self._tag_combo = QComboBox()
        self._tag_combo.setAccessibleName("Filter by tag")
        self._tag_combo.setFixedWidth(140)
        self._tag_combo.currentIndexChanged.connect(self._refresh_table)
        filter_row.addWidget(self._tag_combo)
        lbl_filter.setBuddy(self._tag_combo)

        from bitnet_launcher.gui.wheel_event_filter import suppress_wheel_on_widgets

        suppress_wheel_on_widgets([self._tag_combo])

        # ⚡ Bolt Optimization: Debounce search input
        # Why: Prevents synchronous disk I/O and layout recalculations on every
        # keystroke, making typing in the search box significantly smoother.
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._refresh_table)

        self._search = QLineEdit()
        self._search.setAccessibleName("Search models")
        self._search.setPlaceholderText("Search by name…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._search_timer.start)
        filter_row.addWidget(self._search)

        root.addLayout(filter_row)

        # Model table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Params", "Size (GB)", "Tags", "Status"]
        )

        # We know QTableWidget has horizontal/vertical headers, but mypy doesn't
        # narrow the type down from QTableView's QHeaderView|None return type
        horizontal_header = self._table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            for col in (1, 2, 4):
                horizontal_header.setSectionResizeMode(
                    col, QHeaderView.ResizeMode.ResizeToContents
                )

        vertical_header = self._table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)

        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_selection_changed)

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
        self._log.setAccessibleName("Download log")
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            f"QTextEdit {{ background: {t.BG}; color: {t.TEXT}; "
            f"border: 1px solid {t.SURFACE}; }} "
            f"QTextEdit:focus {{ border: 1px solid {t.ACCENT}; }}"
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
        self._btn_download.setToolTip("Select a model to download")
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
        if model.name not in self._installed_cache:
            gguf = self._models_dir / model.name / "ggml-model-i2_s.gguf"
            self._installed_cache[model.name] = gguf.exists()
        return self._installed_cache[model.name]

    # ── Table population ─────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        """Repopulate the table according to current filter settings."""
        self._visible_models = self._filtered_models()

        # ⚡ Bolt Optimization: Suspend table updates during batch insertions
        # Why: Prevents expensive synchronous layout recalculations and repaints
        # for every single cell inserted, drastically improving rendering speed.
        self._table.setUpdatesEnabled(False)
        try:
            self._table.setRowCount(len(self._visible_models))

            for row, model in enumerate(self._visible_models):
                installed = self._is_installed(model)

                name_item = QTableWidgetItem(model.name)
                name_item.setFont(self._font_consolas_9)
                self._table.setItem(row, 0, name_item)

                self._table.setItem(row, 1, QTableWidgetItem(model.params))
                self._table.setItem(row, 2, QTableWidgetItem(f"{model.size_gb:.1f}"))
                self._table.setItem(row, 3, QTableWidgetItem(", ".join(model.tags)))

                status_item = QTableWidgetItem("Installed" if installed else "—")
                if installed:
                    status_item.setForeground(self._color_green)
                else:
                    status_item.setForeground(self._color_subtext)
                self._table.setItem(row, 4, status_item)
        finally:
            self._table.setUpdatesEnabled(True)

        self._btn_download.setEnabled(False)
        self._btn_download.setToolTip("Select a model to download")
        self._detail_label.setText("")

    def _on_selection_changed(self) -> None:
        """Update the detail label and download button when selection changes."""
        selection_model = self._table.selectionModel()
        rows = selection_model.selectedRows() if selection_model is not None else []
        if not rows:
            self._btn_download.setEnabled(False)
            self._btn_download.setToolTip("Select a model to download")
            self._detail_label.setText("")
            return
        row = rows[0].row()
        if row >= len(self._visible_models):
            return
        model = self._visible_models[row]
        installed = self._is_installed(model)
        name_esc = html.escape(model.name)
        desc_esc = html.escape(model.description)
        repo_esc = html.escape(model.repo_id)
        self._detail_label.setText(
            f"<b>{name_esc}</b> — {model.params} params, "
            f"{model.size_gb:.1f} GB download<br>"
            f"{desc_esc}<br>"
            f"<i>HF repo: {repo_esc}</i>"
        )
        self._btn_download.setEnabled(not installed and self._worker is None)
        if installed:
            self._btn_download.setToolTip("Model is already installed")
        elif self._worker is not None:
            self._btn_download.setToolTip("A download is already in progress")
        else:
            self._btn_download.setToolTip("Download this model")

    # ── Download ─────────────────────────────────────────────────────────────

    def _selected_model(self) -> HubModel | None:
        """Return the currently selected :class:`~bitnet_launcher.hub.HubModel`."""
        selection_model = self._table.selectionModel()
        rows = selection_model.selectedRows() if selection_model is not None else []
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
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("BitNet not found")
            msg.setTextFormat(Qt.TextFormat.PlainText)
            msg.setText(
                f"setup_env.py not found at:\n{self._bitnet_root}\n\n"
                "Use the Setup dialog to install BitNet first."
            )
            msg.exec()
            return

        self._log.clear()
        self._progress.setValue(0)
        self._btn_download.setEnabled(False)
        self._btn_download.setToolTip("A download is currently in progress")
        self._btn_close.setEnabled(False)
        self._btn_close.setToolTip("A download is currently in progress")
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
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log.setTextCursor(cursor)
        doc = self._log.document()
        if doc is not None and not doc.isEmpty():
            self._log.insertPlainText("\n")
        self._log.insertPlainText(line)

    def _on_progress(self, value: float) -> None:
        """Update the progress bar (0.0–1.0)."""
        self._progress.setValue(int(value * 100))

    def _on_download_finished(self) -> None:
        """Handle successful download completion."""
        self._progress.setValue(100)
        self._append_log("Download complete.")
        self._worker = None
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")
        self._installed_cache.clear()
        self._refresh_table()
        logger.info("Download worker finished successfully")

    def _on_download_error(self, message: str) -> None:
        """Handle download failure."""
        self._append_log(f"ERROR: {message}")
        self._worker = None
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")
        self._on_selection_changed()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Download Failed")
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.setText(message)
        msg.exec()
        logger.error("Download worker error: %s", message)

    def reject(self) -> None:  # type: ignore[override]
        """Block closing while a download is in progress."""
        if self._worker is not None and self._worker.isRunning():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Download in Progress")
            msg.setTextFormat(Qt.TextFormat.PlainText)
            msg.setText("Please wait for the download to finish.")
            msg.exec()
            return
        super().reject()

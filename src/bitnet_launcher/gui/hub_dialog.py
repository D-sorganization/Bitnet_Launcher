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
import os
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
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

        self._setup_env_exists = (self._bitnet_root / "setup_env.py").exists()

        self.setWindowTitle("Download BitNet Models")
        self.resize(820, 640)
        self.setStyleSheet(get_hub_dialog_stylesheet())
        self._build_ui()
        self._populate_tag_filter()
        self._refresh_table()
        self._search.setFocus()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Filter row
        filter_row = QHBoxLayout()
        lbl_filter = QLabel("&Filter:")
        filter_row.addWidget(lbl_filter)

        self._tag_combo = QComboBox()
        self._tag_combo.setAccessibleName("Filter by tag")
        lbl_filter.setBuddy(self._tag_combo)
        self._tag_combo.setToolTip(
            "Filter the model list by specific capabilities or sizes"
        )
        if self._tag_combo.toolTip():
            lbl_filter.setToolTip(self._tag_combo.toolTip())
        self._tag_combo.setFixedWidth(140)
        self._tag_combo.currentIndexChanged.connect(self._refresh_table)
        filter_row.addWidget(self._tag_combo)

        from bitnet_launcher.gui.wheel_event_filter import suppress_wheel_on_widgets

        suppress_wheel_on_widgets([self._tag_combo])

        # ⚡ Bolt Optimization: Debounce search input
        # Why: Prevents synchronous disk I/O and layout recalculations on every
        # keystroke, making typing in the search box significantly smoother.
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._refresh_table)

        lbl_search = QLabel("&Search:")
        filter_row.addWidget(lbl_search)

        self._search = QLineEdit()
        lbl_search.setBuddy(self._search)
        self._search.setAccessibleName("Search models")
        self._search.setPlaceholderText("Search by name…")
        self._search.setToolTip("Filter models by name")
        if self._search.toolTip():
            lbl_search.setToolTip(self._search.toolTip())
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._search_timer.start)
        filter_row.addWidget(self._search)

        root.addLayout(filter_row)

        # Model table
        self._table = QTableWidget(0, 5)
        self._table.setAccessibleName("Available Models")
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
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
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)

        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_selection_changed)

        self._table.itemActivated.connect(self._on_item_activated)

        root.addWidget(self._table)

        # Detail label
        self._detail_label = QLabel()
        self._detail_label.setWordWrap(True)
        self._detail_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
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
        # Security: Prevent HTML injection/UI redressing from log outputs
        self._log.setAcceptRichText(False)
        self._log.setAccessibleName("Download log")
        self._log.setAcceptRichText(False)
        self._log.setPlaceholderText("Download logs will appear here...")
        self._log.setReadOnly(True)
        self._log.setTabChangesFocus(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            f"QTextEdit {{ background: {t.BG}; color: {t.TEXT}; "
            f"border: 1px solid {t.SURFACE}; }} "
            f"QTextEdit:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        log_layout.addWidget(self._log)

        self._progress = QProgressBar()
        self._progress.setAccessibleName("Download progress")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        log_layout.addWidget(self._progress)

        root.addWidget(log_group)

        # Button row
        btn_row = QHBoxLayout()
        self._btn_close = QPushButton("&Close")
        self._btn_close.setAccessibleName("Close")
        self._btn_close.setFixedHeight(32)
        self._btn_close.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_close)

        btn_row.addStretch()

        self._btn_download = QPushButton("⬇  &Download Selected")
        self._btn_download.setAccessibleName("Download Selected")
        self._btn_download.setFixedHeight(32)
        self._btn_download.setEnabled(False)
        self._btn_download.setToolTip("Select a model to download")
        self._btn_download.setStyleSheet(
            f"QPushButton {{ color: {t.GREEN}; border-color: {t.GREEN}; }}"
            f"QPushButton:hover {{ background: #1e3a2f; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
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
        """Return ``True`` if the model's GGUF file already exists.

        Prebuilt-GGUF models (``gguf_file`` set) are checked against that
        filename; setup_env.py-quantized models use ``ggml-model-i2_s.gguf``.
        """
        if model.name not in self._installed_cache:
            model_dir = self._models_dir / model.name
            if model.gguf_file is not None:
                installed = (model_dir / model.gguf_file).exists()
                # Tolerate filename drift (the downloader may fall back to a
                # differently-named *tq2_0*.gguf).
                if not installed and model_dir.is_dir():
                    # ⚡ Bolt Optimization: os.scandir is ~4-5x faster than
                    # Path.iterdir() + glob
                    with os.scandir(model_dir) as it:
                        installed = any(
                            (lname := f.name.lower()).endswith(".gguf")
                            and "tq2_0" in lname
                            for f in it
                        )

            else:
                installed = (model_dir / "ggml-model-i2_s.gguf").exists()
            self._installed_cache[model.name] = installed
        return self._installed_cache[model.name]

    # ── Table population ─────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        """Repopulate the table according to current filter settings."""
        # ⚡ Bolt Optimization: Removed synchronous disk I/O `Path.exists()` check.
        # Why: Prevents UI micro-stutters on every keystroke during filtering.
        # `_setup_env_exists` is cached during `__init__` and doesn't change here.
        self._visible_models = self._filtered_models()

        # ⚡ Bolt Optimization: Suspend table updates during batch insertions
        # Why: Prevents expensive synchronous layout recalculations and repaints
        # for every single cell inserted, drastically improving rendering speed.
        self._table.setUpdatesEnabled(False)
        try:
            self._table.clearSpans()
            if not self._visible_models:
                self._table.setToolTip("")
                self._table.setRowCount(1)
                empty_item = QTableWidgetItem("No models match your filter.")
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_item.setForeground(self._color_subtext)
                self._table.setItem(0, 0, empty_item)
                self._table.setSpan(0, 0, 1, 5)
            else:
                self._table.setToolTip("Double-click or press Enter to download")
                self._table.setRowCount(len(self._visible_models))

                for row, model in enumerate(self._visible_models):
                    installed = self._is_installed(model)

                    # ⚡ Bolt Optimization: Reuse QTableWidgetItem objects
                    # Why: Prevents excessive memory allocations and main-thread lag
                    # by reusing existing items in the table when repopulating.
                    name_item = self._table.item(row, 0)
                    if name_item is None:
                        name_item = QTableWidgetItem(model.name)
                        name_item.setFont(self._font_consolas_9)
                        self._table.setItem(row, 0, name_item)
                    else:
                        name_item.setText(model.name)

                    params_item = self._table.item(row, 1)
                    if params_item is None:
                        self._table.setItem(row, 1, QTableWidgetItem(model.params))
                    else:
                        params_item.setText(model.params)

                    size_item = self._table.item(row, 2)
                    if size_item is None:
                        self._table.setItem(
                            row, 2, QTableWidgetItem(f"{model.size_gb:.1f}")
                        )
                    else:
                        size_item.setText(f"{model.size_gb:.1f}")

                    tags_item = self._table.item(row, 3)
                    if tags_item is None:
                        self._table.setItem(
                            row, 3, QTableWidgetItem(", ".join(model.tags))
                        )
                    else:
                        tags_item.setText(", ".join(model.tags))

                    status_item = self._table.item(row, 4)
                    status_text = "Installed" if installed else "—"
                    if status_item is None:
                        status_item = QTableWidgetItem(status_text)
                        self._table.setItem(row, 4, status_item)
                    else:
                        status_item.setText(status_text)

                    if installed:
                        status_item.setForeground(self._color_green)
                    else:
                        status_item.setForeground(self._color_subtext)
        finally:
            self._table.setUpdatesEnabled(True)

        if not self._setup_env_exists:
            self._btn_download.setEnabled(False)
            self._btn_download.setToolTip(
                "BitNet not installed. Use the Setup dialog first."
            )
        else:
            self._btn_download.setEnabled(False)
            self._btn_download.setToolTip("Select a model to download")

        self._detail_label.setText("")

    def _on_selection_changed(self) -> None:
        """Update the detail label and download button when selection changes."""
        selection_model = self._table.selectionModel()
        rows = selection_model.selectedRows() if selection_model is not None else []
        if not rows:
            if not self._setup_env_exists:
                self._btn_download.setEnabled(False)
                self._btn_download.setToolTip(
                    "BitNet not installed. Use the Setup dialog first."
                )
            else:
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
        params_esc = html.escape(str(model.params))
        self._detail_label.setText(
            f"<b>{name_esc}</b> — {params_esc} params, "
            f"{model.size_gb:.1f} GB download<br>"
            f"{desc_esc}<br>"
            f"<i>HF repo: {repo_esc}</i>"
        )
        if not self._setup_env_exists:
            self._btn_download.setEnabled(False)
            self._btn_download.setToolTip(
                "BitNet not installed. Use the Setup dialog first."
            )
        else:
            self._btn_download.setEnabled(not installed and self._worker is None)
            if installed:
                self._btn_download.setToolTip("Model is already installed")
            elif self._worker is not None:
                self._btn_download.setToolTip("A download is already in progress")
            else:
                self._btn_download.setToolTip("Download this model")

    def _on_item_activated(self) -> None:
        """Handle item activation (double-click or Enter) to start download."""
        if self._btn_download.isEnabled():
            self._start_download()

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

        self._log.clear()
        self._progress.setValue(0)
        self._btn_download.setEnabled(False)
        self._btn_download.setText("⏳ Downloading...")
        self._btn_download.setAccessibleName("Downloading...")
        self._btn_download.setToolTip("A download is currently in progress")
        self._btn_close.setEnabled(False)
        self._btn_close.setToolTip("A download is currently in progress")

        self._search.setEnabled(False)
        self._search.setToolTip("An operation is currently in progress")
        self._tag_combo.setEnabled(False)
        self._tag_combo.setToolTip("An operation is currently in progress")
        self._table.setEnabled(False)
        self._table.setToolTip("An operation is currently in progress")
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
        # ⚡ Bolt Optimization: For high-frequency, whole-line appending to a QTextEdit,
        # use .append(html.escape(line)) rather than QTextCursor manipulations.
        # This handles paragraph creation and scrolling more efficiently without
        # causing main-thread layout recalculation stuttering.
        self._log.append(html.escape(line))

    def _on_progress(self, value: float) -> None:
        """Update the progress bar (0.0–1.0)."""
        self._progress.setValue(int(value * 100))

    def _on_download_finished(self) -> None:
        """Handle successful download completion."""
        self._progress.setValue(100)
        self._append_log("Download complete.")
        self._worker = None
        self._btn_download.setText("⬇  &Download Selected")
        self._btn_download.setAccessibleName("Download Selected")
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")

        self._search.setEnabled(True)
        self._search.setToolTip("Filter models by name")
        self._tag_combo.setEnabled(True)
        self._tag_combo.setToolTip(
            "Filter the model list by specific capabilities or sizes"
        )
        self._table.setEnabled(True)
        self._table.setToolTip(
            "Double-click or press Enter to download" if self._visible_models else ""
        )

        self._installed_cache.clear()
        self._refresh_table()
        logger.info("Download worker finished successfully")

    def _on_download_error(self, message: str) -> None:
        """Handle download failure."""
        self._append_log(f"ERROR: {message}")
        self._worker = None
        self._btn_download.setText("⬇  &Download Selected")
        self._btn_download.setAccessibleName("Download Selected")
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")

        self._search.setEnabled(True)
        self._search.setToolTip("Filter models by name")
        self._tag_combo.setEnabled(True)
        self._tag_combo.setToolTip(
            "Filter the model list by specific capabilities or sizes"
        )
        self._table.setEnabled(True)
        self._table.setToolTip(
            "Double-click or press Enter to download" if self._visible_models else ""
        )

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

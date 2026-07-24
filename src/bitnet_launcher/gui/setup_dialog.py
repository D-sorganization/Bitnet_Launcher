"""Installation setup dialog for BitNet Launcher.

:class:`SetupDialog` lets the user inspect the current BitNet installation,
change the BitNet root directory, run a git clone + pip install via
:func:`~bitnet_launcher.installer.install_bitnet`, and trigger the cmake
build via :func:`~bitnet_launcher.installer.build_bitnet`.

All subprocess operations run in a :class:`InstallerWorker` ``QThread`` so
the GUI remains responsive during long-running steps.
"""

from __future__ import annotations

import html
import logging
from enum import Enum, auto
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.installer import (
    InstallStatus,
    build_bitnet,
    check_installation,
    install_bitnet,
)
from bitnet_launcher.theme import CatppuccinTheme

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class _WorkerMode(Enum):
    INSTALL = auto()
    BUILD = auto()


class InstallerWorker(QThread):
    """Worker thread for :func:`~bitnet_launcher.installer.install_bitnet`
    and :func:`~bitnet_launcher.installer.build_bitnet`.

    Signals
    -------
    log_line(str):
        Emitted for each line of subprocess output.
    finished():
        Emitted on successful completion.
    error(str):
        Emitted with a description if the operation fails.
    """

    log_line = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        mode: _WorkerMode,
        bitnet_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise the worker.

        Parameters
        ----------
        mode:
            Whether to run the install or the build step.
        bitnet_root:
            Path used as either the install target (INSTALL) or the
            existing checkout root (BUILD).
        parent:
            Optional Qt parent.
        """
        super().__init__(parent)
        self._mode = mode
        self._bitnet_root = bitnet_root

    def run(self) -> None:
        """Execute the chosen operation in the worker thread."""
        try:
            if self._mode == _WorkerMode.INSTALL:
                install_bitnet(self._bitnet_root, on_log=self.log_line.emit)
            else:
                build_bitnet(self._bitnet_root, on_log=self.log_line.emit)
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("InstallerWorker error: %s", exc)
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

_CHECK_MARK = "\u2713"
_CROSS_MARK = "\u2717"


class SetupDialog(QDialog):
    """Dialog for inspecting and managing the BitNet installation.

    Parameters
    ----------
    bitnet_root:
        Current BitNet root path (can be changed via the path editor).
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        bitnet_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        if not isinstance(bitnet_root, Path):
            raise TypeError(
                f"bitnet_root must be a Path, got {type(bitnet_root).__name__}"
            )
        super().__init__(parent)
        self._bitnet_root = bitnet_root
        self._worker: InstallerWorker | None = None

        self.setWindowTitle("BitNet Setup")
        self.resize(640, 580)
        self.setStyleSheet(_dialog_stylesheet())
        self._build_ui()
        self._refresh_status()
        self._path_edit.setFocus()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ── Status group ─────────────────────────────────────────────────────
        status_group = QGroupBox("Installation Status")
        status_layout = QVBoxLayout(status_group)

        self._lbl_root = QLabel()
        self._lbl_llama = QLabel()
        self._lbl_models = QLabel()
        self._lbl_deps = QLabel()
        self._lbl_setup_env = QLabel()

        for lbl in (
            self._lbl_root,
            self._lbl_llama,
            self._lbl_models,
            self._lbl_deps,
            self._lbl_setup_env,
        ):
            lbl.setWordWrap(True)
            status_layout.addWidget(lbl)

        root.addWidget(status_group)

        # ── Path editor ──────────────────────────────────────────────────────
        path_group = QGroupBox("BitNet Root")
        path_layout = QHBoxLayout(path_group)

        self._path_edit = QLineEdit(str(self._bitnet_root))
        self._path_edit.setPlaceholderText("/home/user/BitNet")
        self._path_edit.setAccessibleName("BitNet Root Path")
        self._path_edit.setClearButtonEnabled(True)
        self._path_edit.editingFinished.connect(self._on_path_edited)
        path_layout.addWidget(self._path_edit)

        btn_browse = QPushButton("…")
        btn_browse.setAccessibleName("Browse for BitNet root directory")
        btn_browse.setFixedWidth(32)
        btn_browse.setToolTip("Choose BitNet root directory")
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)

        root.addWidget(path_group)

        # ── Action buttons ───────────────────────────────────────────────────
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self._btn_install = QPushButton("&Install BitNet (git clone + pip)")
        self._btn_install.setAccessibleName("Install BitNet")
        self._btn_install.setFixedHeight(34)
        self._btn_install.setToolTip(
            "Clone the BitNet repository and install Python dependencies"
        )
        self._btn_install.setStyleSheet(
            f"QPushButton {{ color: {t.ACCENT}; border-color: {t.ACCENT}; }}"
            f"QPushButton:hover {{ background: #2e2342; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_install.clicked.connect(self._start_install)
        actions_layout.addWidget(self._btn_install)

        self._btn_build = QPushButton("&Build BitNet (cmake)")
        self._btn_build.setAccessibleName("Build BitNet")
        self._btn_build.setFixedHeight(34)
        self._btn_build.setToolTip("Compile llama-cli from source using cmake")
        self._btn_build.setStyleSheet(
            f"QPushButton {{ color: {t.YELLOW}; border-color: {t.YELLOW}; }}"
            f"QPushButton:hover {{ background: #3a341e; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_build.clicked.connect(self._start_build)
        actions_layout.addWidget(self._btn_build)

        root.addWidget(actions_group)

        # ── Log ──────────────────────────────────────────────────────────────
        log_group = QGroupBox("Log output")
        log_layout = QVBoxLayout(log_group)

        self._log = QTextEdit()
        self._log.setAccessibleName("Setup log")
        self._log.setPlaceholderText("Setup logs will appear here...")
        self._log.setReadOnly(True)
        self._log.setTabChangesFocus(True)
        self._log.setStyleSheet(
            f"QTextEdit {{ background: {t.BG}; color: {t.TEXT}; "
            f"border: 1px solid {t.SURFACE}; }} "
            f"QTextEdit:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        log_layout.addWidget(self._log)

        root.addWidget(log_group)

        # ── Close button ─────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_close = QPushButton("&Close")
        self._btn_close.setAccessibleName("Close")
        self._btn_close.setFixedHeight(32)
        self._btn_close.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_close)
        root.addLayout(btn_row)

    # ── Status refresh ───────────────────────────────────────────────────────

    def _refresh_status(self) -> None:
        """Re-check the installation and update all status labels."""
        status: InstallStatus = check_installation(self._bitnet_root)
        t = CatppuccinTheme
        self._apply_status_label(
            self._lbl_root, status.root_exists, "BitNet directory found"
        )
        self._apply_status_label(
            self._lbl_llama, status.llama_cli_exists, "llama-cli binary built"
        )
        self._apply_status_label(
            self._lbl_models, status.models_dir_exists, "Models directory exists"
        )
        self._apply_status_label(
            self._lbl_deps, status.python_deps_ok, "Python deps (huggingface_hub)"
        )
        self._apply_status_label(
            self._lbl_setup_env, status.setup_env_exists, "setup_env.py present"
        )
        _ = t  # keep import used

        if not status.root_exists:
            self._btn_build.setEnabled(False)
            self._btn_build.setToolTip(
                "BitNet root does not exist. Run the Install step first."
            )
        elif self._worker is None:
            self._btn_build.setEnabled(True)
            self._btn_build.setToolTip("Compile llama-cli from source using cmake")

    def _apply_status_label(self, lbl: QLabel, ok: bool, text: str) -> None:
        """Set *lbl* text and colour according to *ok*."""
        t = CatppuccinTheme
        mark = _CHECK_MARK if ok else _CROSS_MARK
        colour = t.GREEN if ok else t.RED
        text_esc = html.escape(text)
        lbl.setText(f'<span style="color:{colour};">{mark}</span>  {text_esc}')

    # ── Path editing ─────────────────────────────────────────────────────────

    def _on_path_edited(self) -> None:
        """Apply the manually typed path and refresh status."""
        self._bitnet_root = Path(self._path_edit.text().strip())
        self._refresh_status()

    def _browse_path(self) -> None:
        """Open a directory picker and apply the chosen path."""
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Select BitNet root directory",
            str(self._bitnet_root),
        )
        if chosen:
            self._bitnet_root = Path(chosen)
            self._path_edit.setText(chosen)
            self._refresh_status()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _start_install(self) -> None:
        """Launch :func:`~bitnet_launcher.installer.install_bitnet` in a worker."""
        if self._bitnet_root.exists():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Directory Exists")
            msg.setTextFormat(Qt.TextFormat.PlainText)
            msg.setText(
                f"{self._bitnet_root} already exists.\n"
                "Continue with git clone anyway? (may fail if non-empty)"
            )
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            reply = msg.exec()
            if reply != QMessageBox.StandardButton.Yes.value:
                return
        self._run_worker(_WorkerMode.INSTALL)

    def _start_build(self) -> None:
        """Launch :func:`~bitnet_launcher.installer.build_bitnet` in a worker."""
        self._run_worker(_WorkerMode.BUILD)

    def _run_worker(self, mode: _WorkerMode) -> None:
        """Create and start an :class:`InstallerWorker`."""
        self._log.clear()
        self._btn_install.setEnabled(False)
        if mode == _WorkerMode.INSTALL:
            self._btn_install.setText("⏳ Installing...")
            self._btn_install.setAccessibleName("Installing...")
        self._btn_install.setToolTip("An operation is currently in progress")
        self._btn_build.setEnabled(False)
        if mode == _WorkerMode.BUILD:
            self._btn_build.setText("⏳ Building...")
            self._btn_build.setAccessibleName("Building...")
        self._btn_build.setToolTip("An operation is currently in progress")
        self._btn_close.setEnabled(False)
        self._btn_close.setToolTip("An operation is currently in progress")

        self._worker = InstallerWorker(mode, self._bitnet_root, parent=self)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()
        logger.info("InstallerWorker started: mode=%s path=%s", mode, self._bitnet_root)

    def _append_log(self, line: str) -> None:
        """Append *line* to the log text area."""
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log.setTextCursor(cursor)
        doc = self._log.document()
        if doc is not None and not doc.isEmpty():
            self._log.insertPlainText("\n")
        self._log.insertPlainText(line)

    def _on_worker_finished(self) -> None:
        """Re-enable controls and refresh status after a successful run."""
        self._worker = None
        self._btn_install.setText("&Install BitNet (git clone + pip)")
        self._btn_install.setAccessibleName("Install BitNet")
        self._btn_install.setEnabled(True)
        self._btn_install.setToolTip(
            "Clone the BitNet repository and install Python dependencies"
        )
        self._btn_build.setText("&Build BitNet (cmake)")
        self._btn_build.setAccessibleName("Build BitNet")
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")
        self._append_log("\n--- Done ---")
        self._refresh_status()
        logger.info("InstallerWorker finished successfully")

    def _on_worker_error(self, message: str) -> None:
        """Handle worker failure."""
        self._worker = None
        self._btn_install.setText("&Install BitNet (git clone + pip)")
        self._btn_install.setAccessibleName("Install BitNet")
        self._btn_install.setEnabled(True)
        self._btn_install.setToolTip(
            "Clone the BitNet repository and install Python dependencies"
        )
        self._btn_build.setText("&Build BitNet (cmake)")
        self._btn_build.setAccessibleName("Build BitNet")
        self._btn_close.setEnabled(True)
        self._btn_close.setToolTip("")
        self._append_log(f"ERROR: {message}")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Operation Failed")
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.setText(message)
        msg.exec()
        self._refresh_status()
        logger.error("InstallerWorker error: %s", message)

    def reject(self) -> None:  # type: ignore[override]
        """Block closing while an operation is in progress."""
        if self._worker is not None and self._worker.isRunning():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Operation in Progress")
            msg.setTextFormat(Qt.TextFormat.PlainText)
            msg.setText("Please wait for the current operation to finish.")
            msg.exec()
            return
        super().reject()


# ---------------------------------------------------------------------------
# Stylesheet helper
# ---------------------------------------------------------------------------


def _dialog_stylesheet() -> str:
    """Return a stylesheet suitable for the setup dialog."""
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
        QLineEdit {{
            background: {t.SURFACE};
            border: 1px solid {t.OVERLAY};
            border-radius: 3px;
            color: {t.TEXT};
            padding: 2px 4px;
        }}
        QLineEdit:focus {{
            border: 1px solid {t.ACCENT};
            outline: none;
        }}
    """

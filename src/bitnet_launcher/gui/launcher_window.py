"""Top-level application window for BitNet Launcher.

Wires together ModelPanel, SettingsPanel, and ChatPanel.  Owns the
QProcess and the ChatSession state machine.
"""

from __future__ import annotations

import logging
import shlex

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.chat_session import ChatSession
from bitnet_launcher.config import BitnetConfig
from bitnet_launcher.gui.chat_panel import ChatPanel
from bitnet_launcher.gui.hub_dialog import HubDialog
from bitnet_launcher.gui.model_panel import ModelPanel
from bitnet_launcher.gui.settings_panel import SettingsPanel
from bitnet_launcher.gui.setup_dialog import SetupDialog
from bitnet_launcher.models import ModelInfo, discover_models
from bitnet_launcher.terminal import build_command, launch_terminal
from bitnet_launcher.theme import CatppuccinTheme, build_stylesheet

logger = logging.getLogger(__name__)


class BitNetLauncher(QMainWindow):
    """Main application window.

    Parameters
    ----------
    bitnet_config:
        Filesystem path configuration.  Defaults to
        :class:`~bitnet_launcher.config.BitnetConfig` with default paths.
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        bitnet_config: BitnetConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cfg = bitnet_config or BitnetConfig()
        self._process: QProcess | None = None
        self._session: ChatSession = ChatSession(
            on_response_chunk=self._on_response_chunk,
            on_ready=self._on_session_ready,
            on_error=self._on_session_error,
        )
        self._models: list[ModelInfo] = discover_models(self._cfg.models_dir)

        self.setWindowTitle("BitNet Launcher")
        self.resize(900, 680)
        self._build_ui()
        self.setStyleSheet(build_stylesheet())

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("BitNet Launcher")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {t.ACCENT};")
        root.addWidget(title)

        # Top splitter: model list | settings
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setChildrenCollapsible(False)

        self._model_panel = ModelPanel(self._models)
        self._model_panel.model_activated.connect(self._on_model_activated)
        top_splitter.addWidget(self._model_panel)

        self._settings_panel = SettingsPanel()
        top_splitter.addWidget(self._settings_panel)
        top_splitter.setSizes([320, 560])

        root.addWidget(top_splitter)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_terminal = QPushButton("\u2b1b  &Launch in Terminal")
        self._btn_terminal.setAccessibleName("Launch in Terminal")
        self._btn_terminal.setFixedHeight(36)
        self._btn_terminal.setToolTip(
            "Open a new Windows Terminal tab running this model"
        )
        self._btn_terminal.setStyleSheet(
            f"QPushButton {{ color: {t.YELLOW}; border-color: {t.YELLOW}; }}"
            f"QPushButton:hover {{ background: #3a341e; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_terminal.clicked.connect(self._launch_terminal)
        btn_row.addWidget(self._btn_terminal)

        self._btn_chat = QPushButton("\U0001f4ac  Chat &Here")
        self._btn_chat.setAccessibleName("Chat Here")
        self._btn_chat.setFixedHeight(36)
        self._btn_chat.setToolTip("Start an embedded chat session in this window")
        self._btn_chat.setStyleSheet(
            f"QPushButton {{ color: {t.GREEN}; border-color: {t.GREEN}; }}"
            f"QPushButton:hover {{ background: #1e3a2f; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_chat.clicked.connect(self._start_chat)
        btn_row.addWidget(self._btn_chat)

        self._btn_stop = QPushButton("\u25a0  St&op")
        self._btn_stop.setAccessibleName("Stop chat")
        self._btn_stop.setFixedHeight(36)
        self._btn_stop.setEnabled(False)
        self._btn_stop.setToolTip("No active chat session to stop")
        self._btn_stop.setStyleSheet(
            f"QPushButton {{ color: {t.RED}; border-color: {t.RED}; }}"
            f"QPushButton:hover {{ background: #3a1e28; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_stop.clicked.connect(self._stop_chat)
        btn_row.addWidget(self._btn_stop)

        # Vertical separator between action groups
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet(f"color: {t.OVERLAY};")
        btn_row.addWidget(sep)

        self._btn_download = QPushButton("\u2b07  &Download Models")
        self._btn_download.setAccessibleName("Download Models")
        self._btn_download.setFixedHeight(36)
        self._btn_download.setToolTip(
            "Browse and download BitNet models from HuggingFace"
        )
        self._btn_download.setStyleSheet(
            f"QPushButton {{ color: {t.ACCENT}; border-color: {t.ACCENT}; }}"
            f"QPushButton:hover {{ background: #2e2342; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_download.clicked.connect(self._open_hub_dialog)
        btn_row.addWidget(self._btn_download)

        self._btn_setup = QPushButton("\u2699  Set&up")
        self._btn_setup.setAccessibleName("Setup")
        self._btn_setup.setFixedHeight(36)
        self._btn_setup.setToolTip(
            "Manage BitNet installation (git clone, cmake build)"
        )
        self._btn_setup.setStyleSheet(
            f"QPushButton {{ color: {t.YELLOW}; border-color: {t.YELLOW}; }}"
            f"QPushButton:hover {{ background: #3a341e; }}"
            f"QPushButton:disabled {{ color: #585b70; border-color: {t.OVERLAY}; }}"
            f"QPushButton:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        self._btn_setup.clicked.connect(self._open_setup_dialog)
        btn_row.addWidget(self._btn_setup)

        root.addLayout(btn_row)

        self._chat_panel = ChatPanel()
        self._chat_panel.message_submitted.connect(self._send_message)
        root.addWidget(self._chat_panel)

        self._status = QLabel("Ready.")
        self._status.setTextFormat(Qt.TextFormat.PlainText)
        self._status.setStyleSheet(
            f"color: {CatppuccinTheme.SUBTEXT}; font-size: 10px;"
        )
        root.addWidget(self._status)

    # ── Dialog launchers ────────────────────────────────────────────────────

    def _open_hub_dialog(self) -> None:
        """Open the model download dialog."""
        dialog = HubDialog(
            models_dir=self._cfg.models_dir,
            bitnet_root=self._cfg.bitnet_root,
            parent=self,
        )
        dialog.exec()
        # Refresh model list in case new models were downloaded
        self._models = discover_models(self._cfg.models_dir)
        logger.debug("Hub dialog closed; model list refreshed")

    def _open_setup_dialog(self) -> None:
        """Open the BitNet installation setup dialog."""
        dialog = SetupDialog(bitnet_root=self._cfg.bitnet_root, parent=self)
        dialog.exec()
        logger.debug("Setup dialog closed")

    def _on_model_activated(self) -> None:
        if self._btn_chat.isEnabled():
            self._start_chat()

    # ── Terminal launch ──────────────────────────────────────────────────────

    def _update_action_buttons(self, *args: object) -> None:
        has_model = self._model_panel.selected_model is not None
        llama_cli_exists = bool(self._cfg.llama_cli and self._cfg.llama_cli.exists())
        is_running = (
            self._process is not None
            and self._process.state() != QProcess.ProcessState.NotRunning
        )

        self._btn_terminal.setEnabled(has_model and llama_cli_exists)
        if not llama_cli_exists:
            self._btn_terminal.setToolTip(
                "BitNet llama-cli not found. Use the Setup dialog first."
            )
        elif not has_model:
            self._btn_terminal.setToolTip("Select a model from the list first")
        else:
            self._btn_terminal.setToolTip(
                "Open a new Windows Terminal tab running this model"
            )

        self._btn_chat.setEnabled(has_model and llama_cli_exists and not is_running)
        if not llama_cli_exists:
            self._btn_chat.setToolTip(
                "BitNet llama-cli not found. Use the Setup dialog first."
            )
        elif not has_model:
            self._btn_chat.setToolTip("Select a model from the list first")
        elif is_running:
            self._btn_chat.setToolTip("A chat session is already running")
        else:
            self._btn_chat.setToolTip("Start an embedded chat session in this window")

        self._btn_stop.setEnabled(is_running)
        self._btn_stop.setToolTip(
            "Stop the current chat session"
            if is_running
            else "No active chat session to stop"
        )

    def _launch_terminal(self) -> None:
        model = self._model_panel.selected_model
        if not model:
            return
        config = self._settings_panel.inference_config
        try:
            launch_terminal(
                self._cfg.llama_cli,
                model,
                config,
                self._cfg.bitnet_root,
                self._cfg.wt_exe,
            )
            self._set_status(f"Opened terminal: {model.name}")
        except FileNotFoundError:
            cmd = build_command(self._cfg.llama_cli, model, config)
            bash_cmd = shlex.join(cmd)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Terminal not found")
            msg.setTextFormat(Qt.TextFormat.PlainText)
            msg.setText(
                f"Could not launch Windows Terminal.\nRun manually:\n\n{bash_cmd}"
            )
            msg.exec()

    # ── Embedded chat ────────────────────────────────────────────────────────

    def _start_chat(self) -> None:
        model = self._model_panel.selected_model
        if not model or (
            self._process and self._process.state() != QProcess.ProcessState.NotRunning
        ):
            return

        self._chat_panel.clear()
        self._session.reset()
        self._session.start_loading()
        self._chat_panel.append_system(f"Loading {model.name}\u2026\n")

        config = self._settings_panel.inference_config
        cmd = build_command(self._cfg.llama_cli, model, config)

        self._process = QProcess(self)
        self._process.setWorkingDirectory(str(self._cfg.bitnet_root))
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_process_finished)
        self._process.start(cmd[0], cmd[1:])

        if not self._process.waitForStarted(3000):
            self._chat_panel.append_system("Error: failed to start llama-cli.\n")
            self._session.reset()
            self._update_action_buttons()
            return

        self._update_action_buttons()
        self._set_status(f"Running: {model.name}")
        logger.info("Chat session started for model: %s", model.name)

    def _on_stdout(self) -> None:
        if self._process is None:
            return
        raw = self._process.readAllStandardOutput().data()
        chunk = raw.decode("utf-8", errors="replace")
        self._session.feed(chunk)

    def _on_stderr(self) -> None:
        if self._process is None:
            return
        if self._session.state == "loading":
            raw = self._process.readAllStandardError().data()
            self._chat_panel.append_dim(raw.decode("utf-8", errors="replace"))

    def _send_message(self, msg: str) -> None:
        if self._session.state != "ready":
            return
        if self._process is None or (
            self._process.state() == QProcess.ProcessState.NotRunning
        ):
            self._chat_panel.append_system("No active session.\n")
            return

        self._chat_panel.input_enabled = False
        self._session.transition_to_generating()
        self._set_status("Generating\u2026")
        self._chat_panel.append_user(msg)
        self._process.write((msg + "\n").encode())

    def _stop_chat(self) -> None:
        if self._process:
            self._process.kill()
        self._on_process_finished(-1, QProcess.ExitStatus.CrashExit)

    def _on_process_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self._chat_panel.input_enabled = False
        self._update_action_buttons()
        self._session.reset()
        self._chat_panel.append_system("\n--- Session ended ---\n")

        self._set_status("Ready.")
        logger.info("Chat process finished (code=%d)", code)

    # ── ChatSession callbacks ────────────────────────────────────────────────

    def _on_response_chunk(self, chunk: str) -> None:
        self._chat_panel.append_assistant(chunk)

    def _on_session_ready(self) -> None:
        if self._session.state == "ready":
            model = self._model_panel.selected_model
            if model is not None:
                self._set_status(f"Running: {model.name}")
            # Only show "ready" banner on the transition from loading
            if not self._chat_panel.input_enabled:
                self._chat_panel.append_system(
                    "\n\u2713 Model ready. Start typing below.\n\n"
                )
            self._chat_panel.input_enabled = True

    def _on_session_error(self, message: str) -> None:
        self._chat_panel.append_system(f"Error: {message}\n")
        logger.error("ChatSession error: %s", message)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        self._status.setText(msg)

    # ── Cleanup ──────────────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        """Kill the child process before closing."""
        if self._process and (
            self._process.state() != QProcess.ProcessState.NotRunning
        ):
            self._process.kill()
            self._process.waitForFinished(2000)
        event.accept()

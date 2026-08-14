"""Chat display and input panel widget.

:class:`ChatPanel` owns the scrollable message history and the user-input
row.  Business logic lives outside this widget; the panel only handles
display and emits the ``message_submitted`` signal.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bitnet_launcher.theme import CatppuccinTheme

logger = logging.getLogger(__name__)


class ChatPanel(QWidget):
    """Widget that displays the conversation and handles user input.

    Signals
    -------
    message_submitted(str):
        Emitted when the user presses Enter or clicks Send with non-empty text.
    """

    message_submitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the chat panel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """
        super().__init__(parent)
        self._build_ui()

        # ⚡ Bolt Optimization: Cache QTextCharFormat objects to prevent instantiating
        # and avoid modifying the global QTextEdit layout state during insertions.
        self._fmt_yellow = QTextCharFormat()
        self._fmt_yellow.setForeground(QColor(CatppuccinTheme.YELLOW))

        self._fmt_green = QTextCharFormat()
        self._fmt_green.setForeground(QColor(CatppuccinTheme.GREEN))

        self._fmt_accent = QTextCharFormat()
        self._fmt_accent.setForeground(QColor(CatppuccinTheme.ACCENT))

        self._fmt_subtext = QTextCharFormat()
        self._fmt_subtext.setForeground(QColor(CatppuccinTheme.SUBTEXT))

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def input_enabled(self) -> bool:
        """Whether the message input field and Send button are enabled."""
        return self._input.isEnabled()

    @input_enabled.setter
    def input_enabled(self, value: bool) -> None:
        """Enable or disable the input row.

        Parameters
        ----------
        value:
            ``True`` to enable, ``False`` to disable.

        Raises
        ------
        TypeError
            If *value* is not a ``bool``.
        """
        if not isinstance(value, bool):
            raise TypeError(f"input_enabled must be bool, got {type(value).__name__}")
        self._input.setEnabled(value)

        if value:
            self._input.setToolTip("")
            self._input.setFocus()
            self._update_send_button_state()
        else:
            self._input.setToolTip("Wait for the current response to finish")
            self._btn_send.setEnabled(False)
            self._btn_send.setToolTip("Wait for the current response to finish")

    def clear(self) -> None:
        """Clear all text from the chat display."""
        self._display.clear()

    def append_user(self, text: str) -> None:
        """Append a user message in yellow.

        Parameters
        ----------
        text:
            The user's message text (no prefix needed; ``You: `` is added).

        Raises
        ------
        TypeError
            If *text* is not a ``str``.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        cursor = self._display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        doc = self._display.document()
        prefix = "\n" if doc is not None and not doc.isEmpty() else ""

        cursor.insertText(f"{prefix}You: {text}", self._fmt_yellow)
        self._display.setTextCursor(cursor)

    def append_assistant(self, text: str) -> None:
        """Stream-append assistant response text in green (no newline prefix).

        Suitable for incremental streaming; text is inserted at the cursor
        rather than appended as a new paragraph.

        Parameters
        ----------
        text:
            Fragment to append.

        Raises
        ------
        TypeError
            If *text* is not a ``str``.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        cursor = self._display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text, self._fmt_green)
        self._display.setTextCursor(cursor)

    def append_system(self, text: str) -> None:
        """Append a system / status message in accent colour.

        Parameters
        ----------
        text:
            Message text.

        Raises
        ------
        TypeError
            If *text* is not a ``str``.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        cursor = self._display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text, self._fmt_accent)
        self._display.setTextCursor(cursor)

    def append_dim(self, text: str) -> None:
        """Append text in a dimmed subtext colour (e.g. stderr loading output).

        Parameters
        ----------
        text:
            Message text.

        Raises
        ------
        TypeError
            If *text* is not a ``str``.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        cursor = self._display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text, self._fmt_subtext)
        self._display.setTextCursor(cursor)

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        t = CatppuccinTheme

        group = QGroupBox("Chat")
        group_layout = QVBoxLayout(group)

        self._display = QTextEdit()
        # Security: Prevent HTML injection/UI redressing from generated text or logs
        self._display.setAcceptRichText(False)
        self._display.setReadOnly(True)
        self._display.setAcceptRichText(False)
        self._display.setTabChangesFocus(True)
        self._display.setAccessibleName("Chat history")
        self._display.setPlaceholderText(
            "No active chat session.\nSelect a model and click 'Chat Here' to begin."
        )
        self._display.setFont(QFont("Consolas", 10))
        self._display.setStyleSheet(
            f"QTextEdit {{ background: {t.BG}; color: {t.TEXT}; "
            f"border: 1px solid {t.SURFACE}; }} "
            f"QTextEdit:focus {{ border: 1px solid {t.ACCENT}; outline: none; }}"
        )
        group_layout.addWidget(self._display)

        input_row = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type your message and press Enter…")
        self._input.setAccessibleName("Message input")
        self._input.setClearButtonEnabled(True)
        self._input.setEnabled(False)
        self._input.setToolTip("Start a chat session to begin typing")
        self._input.setFont(QFont("Consolas", 10))
        self._input.returnPressed.connect(self._on_submit)
        self._input.textChanged.connect(self._update_send_button_state)
        input_row.addWidget(self._input)

        self._btn_send = QPushButton("Se&nd")
        self._btn_send.setAccessibleName("Send")
        self._btn_send.setFixedWidth(70)
        self._btn_send.setEnabled(False)
        self._btn_send.setToolTip("Start a chat session to send messages")
        self._btn_send.clicked.connect(self._on_submit)
        input_row.addWidget(self._btn_send)

        group_layout.addLayout(input_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

    def _update_send_button_state(self) -> None:
        """Update the enabled state and tooltip of the Send button."""
        if not self._input.isEnabled():
            return

        has_text = bool(self._input.text().strip())
        self._btn_send.setEnabled(has_text)
        if has_text:
            self._btn_send.setToolTip("Send message")
        else:
            self._btn_send.setToolTip("Type a message to send")

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        logger.debug("ChatPanel: message submitted")
        self.message_submitted.emit(text)

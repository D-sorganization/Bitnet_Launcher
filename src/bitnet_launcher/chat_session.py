"""Pure-Python state machine for parsing llama-cli stdout.

:class:`ChatSession` has **no Qt dependency**.  It accepts raw bytes/text
chunks via :meth:`~ChatSession.feed` and fires registered callbacks when
interesting events occur (response chunk available, model ready, error).

State diagram::

    idle → loading → ready ↔ generating

- **idle**: no process running.
- **loading**: process started, buffering stdout until the first prompt.
- **ready**: waiting for a user message.
- **generating**: user message sent, streaming the response.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Sentinel strings emitted by llama-cli
LLAMA_PROMPT: str = "\n> "
ASSISTANT_MARKER: str = "<|im_start|>assistant\n"
IM_END_MARKER: str = "<|im_end|>"

# Hold back this many characters while streaming to avoid splitting a marker
_LOOKAHEAD: int = 30

_VALID_STATES = frozenset({"idle", "loading", "ready", "generating"})


class ChatSession:
    """State machine that parses llama-cli stdout.

    Parameters
    ----------
    on_response_chunk:
        Called with each streamed response text fragment.
    on_ready:
        Called (with no arguments) when the model signals readiness.
    on_error:
        Called with an error description string.
    """

    LLAMA_PROMPT: str = LLAMA_PROMPT
    ASSISTANT_MARKER: str = ASSISTANT_MARKER

    def __init__(
        self,
        on_response_chunk: Callable[[str], None],
        on_ready: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        if not callable(on_response_chunk):
            raise TypeError("on_response_chunk must be callable")
        if not callable(on_ready):
            raise TypeError("on_ready must be callable")
        if not callable(on_error):
            raise TypeError("on_error must be callable")

        self._on_response_chunk = on_response_chunk
        self._on_ready = on_ready
        self._on_error = on_error

        self._state: str = "idle"
        self._stdout_buf: str = ""
        self._echo_done: bool = False

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def state(self) -> str:
        """Current state: ``idle`` | ``loading`` | ``ready`` | ``generating``."""
        return self._state

    def start_loading(self) -> None:
        """Transition from *idle* to *loading*.

        Call this immediately after the llama-cli process is started.

        Raises
        ------
        ValueError
            If the session is not in the *idle* state.
        """
        if self._state != "idle":
            raise ValueError(
                f"start_loading() requires idle state, current: {self._state}"
            )
        self._state = "loading"
        self._stdout_buf = ""
        self._echo_done = False
        logger.debug("ChatSession: idle → loading")

    def transition_to_generating(self) -> None:
        """Transition from *ready* to *generating*.

        Call this when the user's message has been written to the process
        stdin.  Resets the echo-filter flag.

        Raises
        ------
        ValueError
            If the session is not in the *ready* state.
        """
        if self._state != "ready":
            raise ValueError(
                f"transition_to_generating() requires ready state, "
                f"current: {self._state}"
            )
        self._state = "generating"
        self._stdout_buf = ""
        self._echo_done = False
        logger.debug("ChatSession: ready → generating")

    def reset(self) -> None:
        """Reset to *idle* state, discarding any buffered output."""
        self._state = "idle"
        self._stdout_buf = ""
        self._echo_done = False
        logger.debug("ChatSession: reset → idle")

    def feed(self, chunk: str) -> None:
        """Feed a raw stdout chunk into the state machine.

        Parameters
        ----------
        chunk:
            Decoded text received from the llama-cli process stdout.

        Raises
        ------
        TypeError
            If *chunk* is not a ``str``.
        """
        if not isinstance(chunk, str):
            raise TypeError(f"chunk must be str, got {type(chunk).__name__}")

        self._stdout_buf += chunk
        self._process_buf()

    # ── Internal state machine ─────────────────────────────────────────────────

    def _process_buf(self) -> None:
        """Drive the state machine against the current buffer contents."""
        if self._state == "loading":
            self._handle_loading()
        elif self._state == "generating":
            self._handle_generating()

    def _handle_loading(self) -> None:
        """Wait for the first ``\\n> `` prompt then transition to *ready*."""
        if LLAMA_PROMPT in self._stdout_buf:
            self._stdout_buf = ""
            self._state = "ready"
            logger.debug("ChatSession: loading → ready")
            self._on_ready()

    def _handle_generating(self) -> None:
        """Filter the user-echo then stream response tokens."""
        # Phase 1: skip everything up to ASSISTANT_MARKER (user-echo filter)
        if not self._echo_done:
            idx = self._stdout_buf.find(ASSISTANT_MARKER)
            if idx < 0:
                # Marker not yet fully received — keep buffering
                return
            # Discard echo; keep only the text after the marker
            self._stdout_buf = self._stdout_buf[idx + len(ASSISTANT_MARKER) :]
            self._echo_done = True

        # Phase 2: stream response until the trailing "\n> " prompt
        if LLAMA_PROMPT in self._stdout_buf:
            end = self._stdout_buf.index(LLAMA_PROMPT)
            response = self._stdout_buf[:end].rstrip()
            if response.endswith(IM_END_MARKER):
                response = response[: -len(IM_END_MARKER)].rstrip()

            self._stdout_buf = ""
            self._echo_done = False
            self._state = "ready"
            logger.debug("ChatSession: generating → ready")

            if response:
                self._on_response_chunk(response + "\n")
            self._on_ready()
        else:
            # Stream safe portion (hold back _LOOKAHEAD chars for partial markers)
            safe_end = max(0, len(self._stdout_buf) - _LOOKAHEAD)
            if safe_end > 0:
                chunk = self._stdout_buf[:safe_end]
                chunk = chunk.replace(IM_END_MARKER, "").replace("<|im_start|>", "")
                if chunk:
                    self._on_response_chunk(chunk)
                self._stdout_buf = self._stdout_buf[safe_end:]

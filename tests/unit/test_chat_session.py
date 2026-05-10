"""Unit tests for bitnet_launcher.chat_session.

Tests cover all state transitions and the echo-filter logic.
No Qt dependency — all tests are headless-safe.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from bitnet_launcher.chat_session import (
    ASSISTANT_MARKER,
    LLAMA_PROMPT,
    ChatSession,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_session() -> tuple[ChatSession, MagicMock, MagicMock, MagicMock]:
    """Return a ChatSession and its three callback mocks."""
    on_chunk = MagicMock()
    on_ready = MagicMock()
    on_error = MagicMock()
    session = ChatSession(
        on_response_chunk=on_chunk,
        on_ready=on_ready,
        on_error=on_error,
    )
    return session, on_chunk, on_ready, on_error


# ── Construction ───────────────────────────────────────────────────────────────


class TestChatSessionInit:
    def test_initial_state_is_idle(self) -> None:
        session, *_ = _make_session()
        assert session.state == "idle"

    def test_non_callable_on_chunk_raises(self) -> None:
        with pytest.raises(TypeError, match="on_response_chunk must be callable"):
            ChatSession(
                on_response_chunk="not_callable",  # type: ignore[arg-type]
                on_ready=lambda: None,
                on_error=lambda e: None,
            )

    def test_non_callable_on_ready_raises(self) -> None:
        with pytest.raises(TypeError, match="on_ready must be callable"):
            ChatSession(
                on_response_chunk=lambda c: None,
                on_ready=42,  # type: ignore[arg-type]
                on_error=lambda e: None,
            )

    def test_non_callable_on_error_raises(self) -> None:
        with pytest.raises(TypeError, match="on_error must be callable"):
            ChatSession(
                on_response_chunk=lambda c: None,
                on_ready=lambda: None,
                on_error=None,  # type: ignore[arg-type]
            )


# ── start_loading ──────────────────────────────────────────────────────────────


class TestStartLoading:
    def test_idle_to_loading(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        assert session.state == "loading"

    def test_start_loading_not_idle_raises(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        with pytest.raises(ValueError, match="requires idle state"):
            session.start_loading()


# ── State: loading ─────────────────────────────────────────────────────────────


class TestLoadingState:
    def test_llama_prompt_transitions_to_ready(self) -> None:
        session, on_chunk, on_ready, _ = _make_session()
        session.start_loading()
        session.feed(f"[loading output]{LLAMA_PROMPT}")
        assert session.state == "ready"
        on_ready.assert_called_once()
        on_chunk.assert_not_called()

    def test_partial_stdout_stays_loading(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        session.feed("model init...")
        assert session.state == "loading"

    def test_preamble_discarded_before_prompt(self) -> None:
        session, on_chunk, on_ready, _ = _make_session()
        session.start_loading()
        # Simulate loading output delivered in two chunks
        session.feed("ggml_init: mem = 1024 MB\n")
        session.feed(f"system_info: ...\n{LLAMA_PROMPT}")
        assert session.state == "ready"
        on_chunk.assert_not_called()


# ── transition_to_generating ───────────────────────────────────────────────────


class TestTransitionToGenerating:
    def _ready_session(self) -> tuple[ChatSession, MagicMock, MagicMock, MagicMock]:
        session, on_chunk, on_ready, on_error = _make_session()
        session.start_loading()
        session.feed(f"preamble{LLAMA_PROMPT}")
        assert session.state == "ready"
        return session, on_chunk, on_ready, on_error

    def test_ready_to_generating(self) -> None:
        session, *_ = self._ready_session()
        session.transition_to_generating()
        assert session.state == "generating"

    def test_not_ready_raises(self) -> None:
        session, *_ = _make_session()
        with pytest.raises(ValueError, match="requires ready state"):
            session.transition_to_generating()


# ── State: generating (echo filter + response streaming) ──────────────────────


class TestGeneratingState:
    def _generating_session(
        self,
    ) -> tuple[ChatSession, MagicMock, MagicMock, MagicMock]:
        session, on_chunk, on_ready, on_error = _make_session()
        session.start_loading()
        session.feed(f"preamble{LLAMA_PROMPT}")
        session.transition_to_generating()
        return session, on_chunk, on_ready, on_error

    def test_full_response_delivered(self) -> None:
        session, on_chunk, on_ready, _ = self._generating_session()
        response = "Hello! How can I help?"
        raw = f"[user echo]{ASSISTANT_MARKER}{response}<|im_end|>{LLAMA_PROMPT}"
        session.feed(raw)

        assert session.state == "ready"
        on_ready.assert_called()
        all_text = "".join(call.args[0] for call in on_chunk.call_args_list)
        assert "Hello! How can I help?" in all_text

    def test_echo_not_included_in_response(self) -> None:
        session, on_chunk, *_ = self._generating_session()
        raw = f"<|im_start|>user\nhi<|im_end|>\n{ASSISTANT_MARKER}Sure!{LLAMA_PROMPT}"
        session.feed(raw)
        all_text = "".join(call.args[0] for call in on_chunk.call_args_list)
        assert "im_start" not in all_text
        assert "im_end" not in all_text
        assert "Sure!" in all_text

    def test_partial_echo_keeps_generating(self) -> None:
        session, on_chunk, *_ = self._generating_session()
        # Send only partial echo — no ASSISTANT_MARKER yet
        session.feed("<|im_start|>user\nhi")
        assert session.state == "generating"
        on_chunk.assert_not_called()

    def test_response_split_across_chunks(self) -> None:
        session, on_chunk, on_ready, _ = self._generating_session()
        echo_and_start = f"echo{ASSISTANT_MARKER}"
        part1 = "Hello, "
        part2 = f"world!{LLAMA_PROMPT}"
        session.feed(echo_and_start + part1)
        session.feed(part2)

        all_text = "".join(call.args[0] for call in on_chunk.call_args_list)
        assert "Hello, " in all_text
        assert "world!" in all_text

    def test_transitions_back_to_ready_after_prompt(self) -> None:
        session, *_ = self._generating_session()
        session.feed(f"{ASSISTANT_MARKER}response{LLAMA_PROMPT}")
        assert session.state == "ready"

    def test_im_end_marker_stripped_from_response(self) -> None:
        session, on_chunk, *_ = self._generating_session()
        raw = f"{ASSISTANT_MARKER}Answer<|im_end|>{LLAMA_PROMPT}"
        session.feed(raw)
        all_text = "".join(call.args[0] for call in on_chunk.call_args_list)
        assert "im_end" not in all_text
        assert "Answer" in all_text


# ── reset ──────────────────────────────────────────────────────────────────────


class TestReset:
    def test_reset_from_loading(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        session.reset()
        assert session.state == "idle"

    def test_reset_from_idle_is_noop(self) -> None:
        session, *_ = _make_session()
        session.reset()
        assert session.state == "idle"

    def test_can_start_loading_after_reset(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        session.reset()
        session.start_loading()
        assert session.state == "loading"


# ── feed() type guard ──────────────────────────────────────────────────────────


class TestFeedTypeGuard:
    def test_feed_non_str_raises(self) -> None:
        session, *_ = _make_session()
        session.start_loading()
        with pytest.raises(TypeError, match="chunk must be str"):
            session.feed(b"bytes")  # type: ignore[arg-type]

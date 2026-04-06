# CLAUDE.md — Bitnet_Launcher

## What This Is

PyQt6 GUI for selecting and chatting with local BitNet LLM models. Wraps the
BitNet llama-cli binary with a model picker, inference settings, embedded chat,
and Windows Terminal launch.

## Key Directories

- `src/bitnet_launcher/` — main package
- `src/bitnet_launcher/gui/` — PyQt6 widgets (no business logic)
- `tests/unit/` — headless-safe unit tests

## Python and Tooling

- **Python 3.11+**. Use `python3`.
- **Formatter:** Ruff format. 88-char line limit.
- **Linter:** Ruff check.

## Dev Commands

```bash
pip install -e ".[dev]"
python3 -m ruff check src/ tests/
python3 -m ruff format src/ tests/
python3 -m mypy src/
python3 -m pytest
python3 -m bitnet_launcher.app   # run the GUI
```

## Architecture Notes

- `chat_session.py` — pure Python state machine, no Qt. Feed raw stdout chunks.
- `gui/` — thin wrappers only; all logic lives in non-Qt modules.
- LOD: GUI panels expose signals/properties; launcher_window never reaches into panel internals.
- DbC: InferenceConfig validates all fields in `__post_init__`. `discover_models()` validates paths.

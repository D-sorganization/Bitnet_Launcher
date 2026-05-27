# CLAUDE.md — Bitnet_Launcher

## Branch Policy

All work on `main` branch. PRs target `main`.

## What This Is

PyQt6 GUI for selecting and chatting with local BitNet LLM models. Wraps the
BitNet llama-cli binary with a model picker, inference settings, embedded chat,
Windows Terminal launch, a HuggingFace model downloader, and a guided
installation manager.

## Key Directories

- `src/bitnet_launcher/` — main package
  - `hub.py` — HuggingFace model catalog and download_model()
  - `installer.py` — InstallStatus, check/install/build helpers
- `src/bitnet_launcher/gui/` — PyQt6 widgets (no business logic)
  - `hub_dialog.py` — model download browser dialog
  - `setup_dialog.py` — installation management dialog
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
- `hub.py` — Qt-free; `download_model()` drives `setup_env.py` as a subprocess.
- `installer.py` — Qt-free; all subprocess streaming via `_run_streaming()` helper.
- `gui/` — thin wrappers only; all logic lives in non-Qt modules.
- LOD: GUI panels expose signals/properties; launcher_window never reaches into panel internals.
- DbC: InferenceConfig validates all fields in `__post_init__`. `discover_models()`, `check_installation()`, and `download_model()` validate paths with TypeError/ValueError.

## Hook bypass policy

**Never use `git commit --no-verify` or `git push --no-verify` unless the hook itself is broken** (tooling not installed, hook script crashes). It is *not* an acceptable workaround for a hook that flags real issues.

### When a hook fails on something you didn't touch

The hook is scoped to *your diff*. If `fleet-fast-guardrails` or any other guardrail reports a violation in a file you didn't change, that's a regression — file an issue against `Repository_Management`. Bypassing locally doesn't help: the same checks run in CI's `quality-gate` and will block the PR.

### When the hook is legitimately broken

Open an issue in `Repository_Management`. If you must bypass once to land an urgent fix, include the hook error in the commit body and link the tracking issue. **Do not normalize `--no-verify` as a workaround.**

### Enforcement

Branch protection requires the CI `quality-gate` check on every PR. That check runs the same lint, format, type, and security gates as the hooks. `--no-verify` only delays feedback — it cannot land code that would have failed the hook.

For the canonical hook contract, see [`Repository_Management/docs/FLEET_HOOK_STANDARDS.md`](https://github.com/D-sorganization/Repository_Management/blob/main/docs/FLEET_HOOK_STANDARDS.md).

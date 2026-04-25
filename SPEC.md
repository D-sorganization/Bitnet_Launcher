# SPEC.md — Bitnet_Launcher

## Identity

- **Repository:** Bitnet_Launcher
- **Version:** 0.1.3
- **Language:** Python 3.11+
- **License:** MIT

## Purpose

PyQt6 desktop GUI for interacting with local BitNet LLM models. Provides:

1. Model discovery (scans a configured models directory for .gguf files)
2. Inference settings (threads, context size, temperature, system prompt)
3. Embedded chat (persistent llama-cli subprocess with state-machine I/O)
4. Terminal launch (opens Windows Terminal tab with interactive session)
5. Model downloading (HuggingFace catalog browser, background download via setup_env.py)
6. Installation management (guided git clone, pip install, and cmake build)

## Non-Goals

- Not a training tool
- Not a server/API — local desktop only
- Not cross-platform (WSL + Windows Terminal specific)

## Architecture

### Modules

| Module                   | Responsibility                                               |
| ------------------------ | ------------------------------------------------------------ |
| `config.py`              | Path config and InferenceConfig dataclass with DbC           |
| `models.py`              | ModelInfo dataclass and model discovery (optimized with `os.scandir`) |
| `chat_session.py`        | llama-cli stdout state machine (Qt-free)                     |
| `terminal.py`            | Command building and terminal launch using `shlex` for safe shell quoting |
| `theme.py`               | Catppuccin colour palette and Qt stylesheet (with explicit focus indicators for accessibility) |
| `hub.py`                 | HubModel catalog (16 models) and download_model() utility    |
| `installer.py`           | InstallStatus, check_installation(), install_bitnet(), build_bitnet() |
| `gui/launcher_window.py` | Top-level QMainWindow — wires all panels and dialogs (with dynamic tooltips) |
| `gui/model_panel.py`     | Scrollable model list widget (with accessible list name)     |
| `gui/settings_panel.py`  | Inference hyperparameter spinboxes (with accessible labels)  |
| `gui/chat_panel.py`      | Chat display and user-input row (with accessible labels)     |
| `gui/hub_dialog.py`      | Model catalog browser and background download dialog (mypy-strict, accessible labels, dynamic tooltips, QTimer-debounced search, cached path checking and Qt objects) |
| `gui/setup_dialog.py`    | Installation status and guided setup dialog (with accessible labels/buttons/focus states) |

`installer.check_installation()` checks optional Python dependency availability
with `importlib.util.find_spec()` so the GUI can report installation status
without importing those packages on the main thread.

### State Machine (ChatSession)

```
idle → loading → ready ↔ generating
```

- **loading**: buffering stdout, waiting for first `\n> `
- **ready**: accepting user input
- **generating**: waiting for `\n> ` after filtering user echo via `<|im_start|>assistant\n`

### Terminal Launch Security

`terminal.launch_terminal()` must quote every dynamic value interpolated into the
`bash -c` script with shell-aware escaping. The llama command argv is rendered
with `shlex.join()`, and the BitNet working directory is rendered with
`shlex.quote(str(bitnet_root))` before it is used in the `cd` command. This
prevents model prompts, model paths, and configured checkout paths from breaking
out of their intended shell arguments.

## Test Configuration

- pytest runs with `-p no:xvfb` to disable the xvfb plugin on self-hosted and headless CI runners where no X display is available

## Repository Hygiene

- Generated Python bytecode artifacts (`__pycache__/`, `*.pyc`, and related files) are ignored and must not be tracked in source control.

# SPEC.md — Bitnet_Launcher

## Identity

- **Repository:** Bitnet_Launcher
- **Version:** 0.1.0
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
| `models.py`              | ModelInfo dataclass and model discovery                      |
| `chat_session.py`        | llama-cli stdout state machine (Qt-free)                     |
| `terminal.py`            | Command building and terminal launch                         |
| `theme.py`               | Catppuccin colour palette and Qt stylesheet                  |
| `hub.py`                 | HubModel catalog (16 models) and download_model() utility    |
| `installer.py`           | InstallStatus, check_installation(), install_bitnet(), build_bitnet() |
| `gui/launcher_window.py` | Top-level QMainWindow — wires all panels and dialogs         |
| `gui/model_panel.py`     | Scrollable model list widget                                 |
| `gui/settings_panel.py`  | Inference hyperparameter spinboxes                           |
| `gui/chat_panel.py`      | Chat display and user-input row                              |
| `gui/hub_dialog.py`      | Model catalog browser and background download dialog (mypy-strict) |
| `gui/setup_dialog.py`    | Installation status and guided setup dialog                  |

### State Machine (ChatSession)

```
idle → loading → ready ↔ generating
```

- **loading**: buffering stdout, waiting for first `\n> `
- **ready**: accepting user input
- **generating**: waiting for `\n> ` after filtering user echo via `<|im_start|>assistant\n`

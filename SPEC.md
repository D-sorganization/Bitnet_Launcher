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

## Non-Goals

- Not a training tool
- Not a server/API — local desktop only
- Not cross-platform (WSL + Windows Terminal specific)

## Architecture

### Modules

| Module            | Responsibility                                          |
| ----------------- | ------------------------------------------------------- |
| `config.py`       | Path config and InferenceConfig dataclass with DbC      |
| `models.py`       | ModelInfo dataclass and model discovery                 |
| `chat_session.py` | llama-cli stdout state machine (Qt-free)                |
| `terminal.py`     | Command building and terminal launch                    |
| `theme.py`        | Catppuccin colour palette and Qt stylesheet             |
| `gui/`            | PyQt6 panels wired by launcher_window                   |

### State Machine (ChatSession)

```
idle → loading → ready ↔ generating
```

- **loading**: buffering stdout, waiting for first `\n> `
- **ready**: accepting user input
- **generating**: waiting for `\n> ` after filtering user echo via `<|im_start|>assistant\n`

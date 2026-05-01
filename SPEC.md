# SPEC.md — Bitnet_Launcher

## Identity

- **Repository:** Bitnet_Launcher
- **Version:** 0.1.4
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
| `gui/launcher_window.py` | Top-level QMainWindow — wires all panels and dialogs (with dynamic tooltips) |
| `gui/model_panel.py`     | Scrollable model list widget (with accessible list name)     |
| `gui/settings_panel.py`  | Inference hyperparameter spinboxes (with accessible labels)  |
| `gui/chat_panel.py`      | Chat display and user-input row (with accessible labels, cached QColor objects, and clear button on input)     |
| `gui/hub_dialog.py`      | Model catalog browser and background download dialog (mypy-strict, accessible labels, dynamic tooltips, accessible progress bar, QTimer-debounced search, cached Qt objects, memory-cached disk I/O, and suspended QTableWidget repaints during batch refresh) |
| `gui/setup_dialog.py`    | Installation status and guided setup dialog (with accessible labels/buttons/focus states, disabled-button dynamic tooltips) |

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


### GUI Security

The application ensures that untrusted string inputs are not evaluated as Rich Text or HTML when appended to `QTextEdit` widgets (like chat history or setup logs) or `QLabel` widgets (like status messages). It prevents XSS/HTML injection by using `insertPlainText()` instead of `append()` for `QTextEdit`, and setting `.setTextFormat(Qt.TextFormat.PlainText)` for `QLabel`. When a `QLabel` requires rich text formatting (using tags like `<b>` or `<br>`), `html.escape()` is manually applied to any untrusted dynamic data injected into the HTML string.

### Terminal Launch Security

`terminal.launch_terminal()` must quote every dynamic value interpolated into the
`bash -c` script with shell-aware escaping. The llama command argv is rendered
with `shlex.join()`, and the BitNet working directory is rendered with
`shlex.quote(str(bitnet_root))` before it is used in the `cd` command. This
prevents model prompts, model paths, and configured checkout paths from breaking
out of their intended shell arguments.

## Test Configuration

- pytest runs with `-p no:xvfb` to disable the xvfb plugin on self-hosted and headless CI runners where no X display is available

## Code Complexity

- McCabe complexity enforcement is enabled via Ruff with a maximum complexity threshold of 10 (C90)
- Violations are enforced at lint time as part of the CI pipeline
- Exceptions for legacy functions may be granted with `# noqa: C901` comments when refactoring is not feasible

## Repository Hygiene

- Generated Python bytecode artifacts (`__pycache__/`, `*.pyc`, and related files) are ignored and must not be tracked in source control.

### UI Improvements
- Model Panel detail labels are explicitly set to `PlainText` format to prevent unintended HTML parsing of dynamically generated file paths and model names.
- Hub Dialog includes dynamic tooltips on the download button explaining its disabled state.
- QLineEdit inputs (such as search inputs) are configured with clear buttons.

### Performance Updates
- Debounced search input to avoid stuttering during rapid typing
- Cached synchronous disk I/O (`Path.exists()`) checks in `HubDialog` to prevent UI freezing during model filtering

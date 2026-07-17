# SPEC.md — Bitnet_Launcher

## Identity

- **Repository:** Bitnet_Launcher
- Version: 0.1.17
- **Language:** Python 3.11+
- **License:** MIT

## Purpose

PyQt6 desktop GUI for interacting with local BitNet LLM models. Provides:

1. Model discovery (scans a configured models directory for .gguf files)
2. Inference settings (threads, context size, temperature, system prompt)
3. Embedded chat (persistent llama-cli subprocess with state-machine I/O)
4. Terminal launch (opens Windows Terminal tab with interactive session)
5. Model downloading (HuggingFace catalog browser; background download via setup_env.py quantization or direct prebuilt-GGUF fetch)
6. Installation management (guided git clone, pip install, and cmake build)

## Non-Goals

- Not a training tool
- Not cross-platform (WSL + Windows Terminal specific)

## Architecture

### Modules

| Module                   | Responsibility                                                                                                                                                                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config.py`              | Path config and InferenceConfig dataclass with DbC                                                                                                                                                                                                                  |
| `models.py`              | ModelInfo dataclass and model discovery                                                                                                                                                                                                                             |
| `chat_session.py`        | llama-cli stdout state machine (Qt-free)                                                                                                                                                                                                                            |
| `terminal.py`            | Command building and terminal launch                                                                                                                                                                                                                                |
| `theme.py`               | Catppuccin colour palette and Qt stylesheet                                                                                                                                                                                                                         |
| `hub.py`                 | HubModel catalog (19 models incl. BitCPM4-CANN) and download_model() (setup_env.py quantize + prebuilt-GGUF fetch) utility                                                                                                                                          |
| `installer.py`           | InstallStatus, check_installation(), install_bitnet(), build_bitnet()                                                                                                                                                                                               |
| `gui/launcher_window.py` | Top-level QMainWindow — wires all panels and dialogs (with dynamic tooltips and accessible names for Unicode-icon buttons)                                                                                                                                          |
| `gui/model_panel.py`     | Scrollable model list widget (with accessible list name and descriptive, unselectable empty state)                                                                                                                                                                  |
| `gui/settings_panel.py`  | Inference hyperparameter spinboxes (with accessible labels)                                                                                                                                                                                                         |
| `gui/chat_panel.py`      | Chat display and user-input row (with accessible labels, cached QColor objects, and clear button on input)                                                                                                                                                          |
| `gui/hub_dialog.py`      | Model catalog browser and background download dialog (mypy-strict, accessible labels, dynamic tooltips, accessible progress bar, accessible names for Unicode-icon buttons, QTimer-debounced search, cached Qt objects, memory-cached disk I/O, suspended repaints) |
| `gui/setup_dialog.py`    | Installation status and guided setup dialog (with accessible labels/buttons/focus states, disabled-button dynamic tooltips, clear button on path input)                                                                                                             |

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

The application ensures that untrusted string inputs are not evaluated as Rich Text or HTML when appended to `QTextEdit` widgets (like chat history or setup logs), `QLabel` widgets (like status messages), or `QMessageBox` popups. It prevents XSS/HTML injection by using `insertPlainText()` instead of `append()` for `QTextEdit`, explicitly setting `.setTextFormat(Qt.TextFormat.PlainText)` for `QLabel` and dynamically instantiated `QMessageBox` objects (rather than using static convenience methods). When a `QLabel` requires rich text formatting (using tags like `<b>` or `<br>`), `html.escape()` is manually applied to any untrusted dynamic data injected into the HTML string.

### Recent Security Updates

- Replaced `QMessageBox` static convenience methods with explicitly instantiated `QMessageBox` objects configured with `setTextFormat(Qt.TextFormat.PlainText)` in `launcher_window.py`, `setup_dialog.py`, and `hub_dialog.py` to prevent potential HTML/Rich Text injection.
- Added `html.escape()` for string-cast `model.params` when interpolating into rich text `QLabel` strings in `hub_dialog.py` to prevent XSS/HTML injection.
- Added `html.escape()` for `text` string when interpolating into a rich text `QLabel` in `setup_dialog.py` (`_apply_status_label`) to prevent XSS/HTML injection.

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

- Chat Panel provides guidance to the user via empty-state placeholder text before a chat session is initiated.
- Model Panel detail labels are explicitly set to `PlainText` format to prevent unintended HTML parsing of dynamically generated file paths and model names.
- Hub Dialog includes dynamic tooltips on the download button explaining its disabled state.
- Dialogs use centralized, shared stylesheets when possible to enforce consistent accessibility features like `:focus` indicators.
- Hub Dialog includes accessible names for its search input, tag filter, and log output.
- Hub Dialog tag filter `QComboBox` is linked to a descriptive buddy label to improve keyboard navigation.
- Hub Dialog table explicitly restricts selection to single-row mode (`setSelectionMode(QTableWidget.SelectionMode.SingleSelection)`) to match its single-action download constraints and prevent visual selection dissonance.
- Chat Panel includes dynamic tooltips on the send button explaining its disabled state.
- Chat Panel includes `:focus` stylesheet rules on read-only displays to preserve keyboard visibility.
- Inline `:focus` styles on interactive widgets (e.g., `QTextEdit`, `QLineEdit`, `QComboBox`, `QTableWidget`) suppress native outlines (`outline: none;`) when a custom accent border is present, preventing duplicate focus rings while keeping keyboard focus visible.
- Setup Dialog includes dynamic tooltips on action buttons explaining their disabled state during long-running operations and when prerequisite installations are missing.
- Hub Dialog includes dynamic tooltips on its close and download buttons, clearing them properly when operations finish, and explaining their disabled states during downloads or when prerequisite installations are missing.
- Setup Dialog includes accessible names on its icon-only browse button and output log.
- Hub Dialog and Setup Dialog log outputs include placeholder text to improve empty-state clarity.
- Inference hyperparameter inputs (QSpinBox) are configured with contextual unit suffixes (e.g. "tokens") to improve clarity.
- Hub Dialog table includes a spanning empty state row with selection disabled when search/filter yields no results.
- Hub Dialog table items can be double-clicked to start a download.
- QLineEdit inputs (such as search inputs) are configured with clear buttons.
- Hub Dialog includes accessible names for its model table and download progress bar to improve screen reader context.
- All `QTextEdit` widgets (Settings Panel, Chat Panel, Setup Dialog log, Hub Dialog log) apply `setTabChangesFocus(True)` to prevent keyboard focus trapping and ensure accessibility.

### Performance Updates

- Debounced search input to avoid stuttering during rapid typing
- Removed synchronous disk I/O (`Path.exists()`) checks from `_refresh_table` in `HubDialog` since it is already cached during `__init__`, preventing UI freezing during model filtering
- Cached `QFont` and `QColor` instantiations in `HubDialog` to prevent redundant object creation during frequent UI refreshes
- Batched updates to `QListWidget` inside `ModelPanel` using `setUpdatesEnabled(False)` to prevent synchronous layout recalculations and improve rendering performance during batch insertions.

### Recent Security Updates

- Replaced `QTextEdit.append()` with safe `insertPlainText()` logic in dialog log outputs to prevent GUI spoofing and XSS vulnerabilities from untrusted subprocess logs.
- Replaced `QMessageBox` static convenience methods with explicitly instantiated `QMessageBox` objects configured with `setTextFormat(Qt.TextFormat.PlainText)` in GUI components to prevent potential HTML/Rich Text injection.
- Added `html.escape()` for string-cast `model.params` when interpolating into rich text `QLabel` strings in `hub_dialog.py` to prevent XSS/HTML injection.
- Added `html.escape()` for `text` string when interpolating into a rich text `QLabel` in `setup_dialog.py` (`_apply_status_label`) to prevent XSS/HTML injection.

## UX Updates

- Auto-focused the primary input fields (`_search` in `HubDialog` and `_path_edit` in `SetupDialog`) immediately upon dialog initialization so that users can start typing their input immediately without needing an extra click.
- Action buttons in the `LauncherWindow` ("Chat Here", "Launch in Terminal") are now proactively disabled when no model is selected from the list or when `llama-cli` is missing, providing dynamic tooltips explaining the state, rather than allowing clicks that result in error dialogs.
- Added unit suffixes to numeric input fields (e.g., " threads" for CPU threads) in the settings panel to provide immediate, inline context and improve readability.
- The "Send" button in the chat panel is now proactively disabled when the chat input is empty, and a tooltip has been added to explain that text is required to send a message.
- Added descriptive tooltips to the "System prompt" field and label in the Settings Panel to explain its purpose to non-technical users.

### API Security Updates

- The FastAPI endpoints `POST /chat/start` and `POST /chat/send` were updated to use Pydantic models in the request body (`ChatStartRequest` and `ChatSendRequest`) rather than accepting URL query parameters. This enforces a `Content-Type: application/json` payload requirement on clients, ensuring that modern browsers send a CORS preflight request (OPTIONS) and protecting the local endpoints from Cross-Site Request Forgery (CSRF) via simple requests.

### Settings Security Updates

- Added a length limitation validation in `InferenceConfig` to reject `system_prompt` values that exceed 4096 characters, mitigating potential Denial of Service (DoS) or memory exhaustion during inference or API usage.

## Model Catalog & Download Updates

- Catalog expanded to 19 models: added OpenBMB BitCPM4-CANN 1B/3B/8B (1.58-bit ternary, llama architecture).
- `HubModel` gained an optional `gguf_file` field. When set, `download_model()` routes to `_download_prebuilt_gguf()`, which fetches the prebuilt `.gguf` directly from the model's `-gguf` HuggingFace repo via `huggingface_hub`, instead of driving `setup_env.py`. This is required for models outside BitNet `setup_env.py`'s fixed `--hf-repo` allow-list.
- The prebuilt download disables HuggingFace Xet (`HF_HUB_DISABLE_XET`) to avoid stalls on large GGUF blobs, and resolves the target filename defensively (falls back to any `*tq2_0*.gguf` in the repo).
- `HubDialog._is_installed()` now recognizes prebuilt-GGUF models by their `gguf_file` (or any `*tq2_0*.gguf`) in addition to `ggml-model-i2_s.gguf`. This utilizes `os.scandir()` instead of `Path.iterdir()` for faster file system traversal.

### Bug Fixes

- Fixed a startup crash in `ModelPanel`: the `currentRowChanged` signal is now connected only after the list is populated and `self._detail` exists, so the initial `setCurrentRow(0)` no longer fires `_on_row_changed` before `_detail` is created (`AttributeError: 'ModelPanel' object has no attribute '_detail'`).
- Explicit maximum length constraints (e.g., `max_length=4096` for messages and `max_length=128` for model names) were added to Pydantic models (`ChatStartRequest` and `ChatSendRequest`) in the API to prevent Denial of Service (DoS) attacks caused by maliciously oversized JSON payloads.

### Keyboard Accessibility

- Added mnemonic ampersands (`&`) to `QLabel` text paired with `setBuddy()` to enable native Alt+Letter keyboard shortcuts for form fields in the Settings and Hub dialogs, improving keyboard accessibility.
- Added a `QLabel` with a mnemonic ampersand (`&`) linked via `setBuddy()` to the search `QLineEdit` in the Hub Dialog, enabling Alt+S navigation.
- Added a placeholder text to the Hub Dialog's log output `QTextEdit` to clarify its empty state.
- Added mnemonic ampersands (`&`) to `QPushButton` text across the Launcher, Hub Dialog, Setup Dialog, and Chat Panel to enable native Alt+Letter keyboard shortcuts for primary action buttons.
- Buttons that include mnemonic ampersands or shortcut text also define clean `setAccessibleName(...)` labels so screen readers announce the action without shortcut punctuation.

### Accessibility

- Added accessible names to the `QSpinBox`, `QDoubleSpinBox`, and `QTextEdit` input fields in the Settings panel (`self._threads`, `self._ctx_size`, `self._temperature`, `self._n_predict`, `self._system_prompt`) using `.setAccessibleName()` without shortcut indicators, ensuring proper screen reader announcements.
- Added `QComboBox` to the input elements styling block and `QComboBox:focus` to the focus styling block in the global Qt stylesheet (`theme.py`) to ensure clear visual focus indicators for keyboard navigation on dropdowns.
- Changed list and table views to use `itemActivated` instead of `itemDoubleClicked` to natively support keyboard activation (Enter/Return) for primary actions.
- Comprehensive disabled states including neutral border colors (`border-color: {t.OVERLAY}`) were added to the `:disabled` pseudo-class for custom-styled buttons across the UI to prevent them from looking active when disabled.
- Added `.setAccessibleName()` explicitly for buttons that use `&` mnemonics (e.g., `_btn_close`, `_btn_install`, `_btn_build`, `_btn_send`) in `hub_dialog.py`, `setup_dialog.py`, and `chat_panel.py` to prevent screen readers from reading the literal ampersand or extraneous text.
- Detail labels in the `ModelPanel` and `HubDialog` have been updated with `Qt.TextInteractionFlag.TextSelectableByMouse` and `Qt.TextInteractionFlag.LinksAccessibleByMouse` to allow users to select and copy text such as file paths and HuggingFace repo IDs.

### API Security Updates

- The FastAPI server (`src/bitnet_launcher/api.py`) was updated to include an HTTP middleware (`add_security_headers`) that enforces essential security headers on all responses, including `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, and `X-XSS-Protection`. This mitigates potential cross-site risks when the local API is running.
- The FastAPI endpoints `POST /chat/start` and `GET /models` were updated to offload blocking file I/O operations (`discover_models`) using `asyncio.to_thread()`, preventing event loop stalls and mitigating Denial of Service (DoS) risks. A robust lock pattern using a `None` placeholder was introduced to the `active_runners` registry to strictly prevent race conditions where concurrent requests for the same model could bypass single-instance checks and spawn multiple orphaned processes.

# BitNet Launcher

A PyQt6 desktop GUI for running local BitNet LLM models. It wraps the
`llama-cli` binary with a model picker, inference settings panel, embedded
chat view, Windows Terminal launch, an integrated model downloader, and a
guided installation manager.

```
[ screenshot placeholder ]
```

---

## Features

- **Model discovery** — scans a configurable models directory for `.gguf` files
- **Inference settings** — threads, context window, temperature, max tokens, and
  system prompt, all validated with DbC
- **Embedded chat** — persistent `llama-cli` subprocess with state-machine I/O;
  streams responses token by token
- **Terminal launch** — opens a new Windows Terminal tab running the selected
  model interactively
- **Model downloader** — HuggingFace catalog browser (all 16 BitNet-compatible
  models) with tag/name filtering and background download via `setup_env.py`
- **Installation manager** — git clone, pip install, and cmake build, all
  driven from inside the app with streaming log output

---

## Requirements

- Python 3.10+
- PyQt6 >= 6.6
- A BitNet checkout at a known path **or** use the built-in Setup dialog to
  install one from scratch

Optional (for the model downloader):

```
pip install "bitnet-launcher[hub]"
```

---

## Quick start

### Path A — you already have BitNet

```bash
git clone <this-repo> Bitnet_Launcher
cd Bitnet_Launcher
pip install -e ".[dev]"
python3 -m bitnet_launcher.app
```

Open the app, verify the default BitNet root points to your checkout, select a
model, and press **Chat Here** or **Launch in Terminal**.

### Path B — fresh install (no BitNet yet)

```bash
pip install -e ".[dev,hub]"
python3 -m bitnet_launcher.app
```

1. Click **Setup** in the toolbar.
2. Set the BitNet root to the desired install location.
3. Click **Install BitNet (git clone + pip)** — wait for it to complete.
4. Click **Build BitNet (cmake)** — this compiles `llama-cli` (~10 min).
5. Close the Setup dialog; the model list will update automatically.
6. Click **Models** to browse and download a model from HuggingFace.

---

## Usage

### Embedded Chat

1. Select a model from the list on the left.
2. Adjust inference settings on the right (threads, context size, temperature).
3. Click **Chat Here**.
4. Type a message and press Enter or click **Send**.
5. Click **Stop** to terminate the session.

### Terminal Session

Select a model and click **Launch in Terminal**. A new Windows Terminal tab
opens with `llama-cli` running interactively. The shell remains open after the
model exits so you can inspect output or re-run.

### Download a Model

Click **Models** to open the download dialog.

- Use the tag filter (`All`, `official`, `reference`, `falcon`, `instruct`, …)
  or the search box to narrow the list.
- Click a row to see the description and size.
- Click **Download Selected** — progress is streamed to the log pane.
- Already-installed models show a green "Installed" status and cannot be
  re-downloaded.

### First-Time Setup

Click **Setup** to open the installation dialog. Status indicators show which
components are present:

| Indicator                     | Meaning                       |
| ----------------------------- | ----------------------------- |
| BitNet directory found        | `bitnet_root` exists          |
| llama-cli binary built        | `build/bin/llama-cli` present |
| Models directory exists       | `models/` present             |
| Python deps (huggingface_hub) | importable                    |
| setup_env.py present          | download script present       |

Use **Browse** to point to an existing checkout or a new empty directory, then
run **Install** (git clone) followed by **Build** (cmake).

---

## Architecture

| Module                   | Responsibility                                                                |
| ------------------------ | ----------------------------------------------------------------------------- |
| `config.py`              | `BitnetConfig` and `InferenceConfig` dataclasses with DbC                     |
| `models.py`              | `ModelInfo` dataclass and `discover_models()` scanner                         |
| `chat_session.py`        | `llama-cli` stdout state machine (Qt-free)                                    |
| `terminal.py`            | Command building and Windows Terminal launch                                  |
| `theme.py`               | Catppuccin Mocha palette and Qt stylesheet                                    |
| `hub.py`                 | `HubModel` catalog (16 models) and `download_model()`                         |
| `installer.py`           | `InstallStatus`, `check_installation()`, `install_bitnet()`, `build_bitnet()` |
| `gui/launcher_window.py` | Top-level `QMainWindow` — wires all panels                                    |
| `gui/model_panel.py`     | Scrollable model list with selection signal                                   |
| `gui/settings_panel.py`  | Inference hyperparameter spinboxes                                            |
| `gui/chat_panel.py`      | Chat display and user-input row                                               |
| `gui/hub_dialog.py`      | Model catalog browser and download dialog                                     |
| `gui/setup_dialog.py`    | Installation status and action dialog                                         |

---

## Development commands

```bash
# Install in editable mode with all dev and hub extras
pip install -e ".[dev,hub]"

# Lint
python3 -m ruff check src/ tests/

# Format
python3 -m ruff format src/ tests/

# Type-check
python3 -m mypy src/

# Test
python3 -m pytest tests/unit/ -q

# Run the GUI
python3 -m bitnet_launcher.app
```

---

## Contributing

1. Branch from `main`; use `feat/`, `fix/`, or `chore/` prefixes.
2. All code must pass `ruff check`, `ruff format --check`, and `pytest tests/unit/`.
3. No `print()` in `src/` — use `logging`.
4. Public functions require type annotations and DbC guards (`TypeError` /
   `ValueError`) on all parameters.
5. GUI files (`gui/`) contain only display logic; subprocess and validation
   logic lives in non-Qt modules.
6. Open a PR against `main`; CI must be green before merging.

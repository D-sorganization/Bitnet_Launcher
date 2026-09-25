# Project Charter

> Drafted 2026-09-25 by the fleet charter sweep (Gemini) from README, git history, and open issues/PRs.
> The project-steward role keeps this current; owners should correct feature statuses.

## End Goal

Bitnet_Launcher is a desktop GUI and local API service for discovering, installing, configuring, downloading, and running quantized BitNet large language models using llama-cli on Windows and WSL. "Done" means a production-ready, fully tested PyQt6 application that allows users to seamlessly clone and build BitNet, download official and community GGUF models from HuggingFace, tweak inference parameters with Design-by-Contract guards, and interact via embedded streaming chat, Windows Terminal, or authenticated local API endpoints with verified security and stability.

## Non-Goals

- Training or fine-tuning models (inference and local deployment only).
- Cross-platform desktop support outside Windows with WSL and Windows Terminal.
- Execution of non-BitNet architectures or arbitrary unsupported model formats.
- Multi-user enterprise cloud serving or remote cluster orchestration.

## Features

| ID | Feature | Status | Tracking | Notes |
| --- | --- | --- | --- | --- |
| F1 | Model discovery | shipped | #17 | Scans configured directory for GGUF models with Windows case-insensitivity |
| F2 | Inference settings panel | shipped | #133 | Hyperparameter controls with DbC validation and system prompt limits |
| F3 | Embedded chat session | shipped | #248 | Subprocess management with stdout state machine and streaming token display |
| F4 | Windows Terminal launch | shipped | - | Launches interactive llama-cli sessions in new Windows Terminal tabs |
| F5 | HuggingFace model downloader | shipped | #279 | Catalog browser and downloader for BitNet models with post-download refresh |
| F6 | Guided installation manager | shipped | #270 | Automated clone, dependency check, and cmake build of BitNet in SetupDialog |
| F7 | Catppuccin theme and accessibility | shipped | #258 | Dark palette styling, keyboard navigation, dynamic tooltips, and selectable labels |
| F8 | GUI and subprocess security | shipped | #224 | Plain-text widget sanitization and shell-safe parameter escaping |
| F9 | Local API service | shipped | #278 | FastAPI endpoints with API key auth, CORS, audit logging, and SSE streaming |
| F10 | Architecture map contract | shipped | #257 | Maintainable Mermaid C4 diagrams and contract validation tooling |
| F11 | Fleet testing alignment | shipped | #85 | Pytest unit test suite covering GUI, runners, and subprocess orchestration |
| F12 | Performance benchmarking | shipped | #36 | Standalone model directory scanning benchmark suite |

## Links

- Status (generated): [`STATUS.md`](STATUS.md)
- Steward playbook: Repository_Management `docs/fleet-project-steward.md`

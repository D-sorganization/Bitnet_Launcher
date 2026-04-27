# AGENTS.md

## 🤖 Agent Personas & Directives

**Audience:** This document is the authoritative guide for AI agents working in this repository.

**Core Mission:**

- Write high-quality, maintainable, and secure PyQt6 desktop application code.
- Adhere strictly to the project's architectural and stylistic standards.
- Act as a responsible pair programmer, always verifying assumptions and testing changes.

---

## 🛡️ Safety & Security (CRITICAL)

1. **Secrets Management**:
   - **NEVER** commit API keys, passwords, tokens, or database connection strings.
   - Use `.env` files and `python-dotenv` for secrets if needed.
   - Create `.env.example` templates for required environment variables.
2. **Subprocess Security**:
   - **NEVER** use `shell=True` in `subprocess` calls.
   - Use list-based arguments for `subprocess.Popen` and `subprocess.run`.
   - Use `shlex.quote()` when dynamic values must be passed to shell-launched processes (like the Windows Terminal integration).
3. **GUI Hygiene**:
   - Prevent XSS/HTML injection by using `insertPlainText()` for `QTextEdit` and `setTextFormat(Qt.TextFormat.PlainText)` for `QLabel`.
4. **Data Protection**:
   - Do not commit large binary files (>50MB) or personal data.

---

## 🐍 Python Coding Standards

### 1. Code Quality & Style

- **Logging vs. Print**:
  - ❌ **DO NOT** use `print()` statements for application output.
  - ✅ **USE** the `logging` module.
- **Imports**:
  - ❌ **NO** wildcard imports (`from module import *`).
  - ✅ **Explicitly** import required classes/functions.
- **Exception Handling**:
  - ❌ **NO** bare `except:` clauses.
  - ✅ **Catch specific exceptions** or at least `except Exception:` with proper logging.
- **Type Hinting**:
  - Use Python type hints for function arguments and return values.

### 2. Testing

- Use `pytest`.
- Run with `-p no:xvfb` on headless environments.
- Target Python 3.11+.

### 3. Design Principles

- **DRY (Don't Repeat Yourself)**: Avoid duplicating UI layout code.
- **Law of Demeter**: Avoid deep chaining of Qt widget access.
- **Single Responsibility**: Keep GUI panels focused on their specific functionality.

---

## 🔄 Git Workflow & Version Control

### 1. Commit Messages

Use **Conventional Commits** format:

- `feat(scope): description`
- `fix(scope): description`
- `docs(scope): description`
- `style(scope): description`
- `refactor(scope): description`
- `test(scope): description`
- `chore(scope): description`

### 2. Pull Requests

- Use **GitHub CLI** (`gh`) for creating and managing PRs.
- Verify all changes pass ruff, black, and mypy locally.

---

## 🏗️ System Architecture

Refer to `SPEC.md` for the detailed module breakdown and responsibility matrix.

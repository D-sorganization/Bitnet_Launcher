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

---

<!-- BEGIN FLEET-MANAGED: reasoning-engagement -->

## 🧠 Reasoning & Engagement

> This section is managed centrally by Repository_Management and synced fleet-wide.
> Do NOT edit it directly in individual repositories — edit the source in Repository_Management/AGENTS.md.

These rules govern _how_ you engage with a task before and during implementation. They exist because LLM agents tend to pick an interpretation silently, overcomplicate the solution, and edit code they were not asked to touch. Each rule directly counteracts one of those failure modes.

- **Surface ambiguity. Do not guess silently.** If the request has more than one plausible interpretation, list the options and ask before implementing. Picking one and running with it is the single most common cause of rework in this fleet.
- **Push back on overcomplication.** If a simpler approach would satisfy the request, say so before you build the complicated one. Do not implement bloated 1000-line constructions when 100 would do. The senior-engineer test: would they call this overcomplicated? If yes, simplify.
- **Stay surgical.** Every changed line must trace directly to the user's request. Do not "improve" adjacent code, comments, formatting, or imports. Do not refactor things that are not broken. Match existing style even if you would do it differently.
- **Spotted ≠ fix.** If you notice unrelated dead code, latent bugs, or stylistic problems while working, _mention them in the PR body or as a follow-up issue_ — do not fix them in the same PR. (The `mcp__ccd_session__spawn_task` tool is the right channel when working interactively.)
- **Clean up only your own orphans.** If your changes leave imports, variables, or functions newly unused, remove them. Do not delete pre-existing dead code unless the task asked for it.
- **State a verifiable success criterion before coding.** For a bug fix, that's a failing test that reproduces it (RED → GREEN, see TDD section below). For a feature, the explicit check that says "done." "Make it work" is not a success criterion.

**The diff test:** every line in your final diff should answer "this is here because the user asked for X." If you cannot answer that for a given line, remove it.

<!-- END FLEET-MANAGED: reasoning-engagement -->

---

<!-- BEGIN FLEET-MANAGED: network-api-hygiene -->

## 🛑 NETWORK & API HYGIENE (CRITICAL)

> This section is managed centrally by Repository_Management and synced fleet-wide.
> Do NOT edit it directly in individual repositories — edit the source in Repository_Management/AGENTS.md.

### GitHub API Quotas

| API Type                  | Quota        | Consumed By                                                        |
| ------------------------- | ------------ | ------------------------------------------------------------------ |
| REST (`gh api repos/...`) | 5,000 req/hr | Safe for polling                                                   |
| GraphQL                   | 5,000 req/hr | `gh pr list --json`, `gh pr checks`, `gh pr create`, `gh pr merge` |

GraphQL and REST have **separate** quotas. Exhausting GraphQL blocks PR creation and merging fleet-wide for an entire hour.

### Mandatory Rules

- **NO MASS POLLING**: Agents MUST NEVER use `gh pr list`, `gh issue list`, or arbitrary REST/GraphQL loops in a bulk manner to "scan" or "sweep" the repository fleet. Single, scoped repository lookups are allowed when needed (e.g., checking if a specific PR exists).
- **LOCAL FIRST**: Rely on local `.md` files, previously generated `issues.json` artifacts, or user assistance to find task context — do not query GitHub to discover what to work on.
- **NO PARALLELIZED GITHUB CLI**: Never write or execute scripts that loop over multiple repositories performing `gh` operations (automated PR merge scripts, fleet-wide status sweeps, etc.).
- **NO TIGHT POLLING LOOPS**: Never implement `while true; do gh pr checks $PR; sleep 30; done` patterns. Each iteration of such a loop costs 1–3 GraphQL calls; at 30-second intervals that drains the 5,000/hr quota in under 3 hours.
  - ❌ `while true; do gh pr checks; sleep 30; done`
  - ✅ `gh run watch <run-id>` — streams CI events without polling
  - ✅ Check status once at natural work breakpoints (after completing other tasks)
- **BATCHING**: If remote information is absolutely necessary, use a single focused query — not a loop of queries.
- **REST OVER GRAPHQL FOR CI STATUS**: Use REST endpoints for CI polling; they don't consume the GraphQL quota.
  - ❌ `gh pr checks <N>` (GraphQL)
  - ✅ `gh api repos/OWNER/REPO/actions/runs` (REST)
  - ✅ `gh api repos/OWNER/REPO/actions/jobs/<id>/logs` (REST)
- **STOP MONITORS IMMEDIATELY**: When using background monitor tasks, call `TaskStop <id>` the moment the monitored condition is satisfied. Do not leave monitors running "just in case."
- **LONG POLLING INTERVALS**: Background monitors must use ≥270-second intervals (keeps the prompt cache warm). Default to 1200–1800 s for idle monitoring. Never chain short sleeps to work around the 60-second minimum.
- **SILENT FAILURES**: If an API rate limit is hit, HALT NETWORK ACTIVITY IMMEDIATELY. Do not write retry-loops that further exhaust the quota. Alert the user and pivot to local work.

### Checking Rate Limit Status

```bash
gh api rate_limit | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)['resources']
for k in ['core', 'graphql']:
    r = d[k]
    reset = datetime.datetime.fromtimestamp(r['reset']).strftime('%H:%M:%S')
    print(f'{k}: {r["remaining"]}/{r["limit"]} remaining — resets {reset}')
"
```

<!-- END FLEET-MANAGED: network-api-hygiene -->


## Closing issues — non-negotiable rule

NEVER close a feature or bug issue without one of:

1. A merged PR that implements the acceptance criteria (use `Closes #N` in the PR body or title), OR
2. An explicit `wontfix`, `roadmap`, `duplicate`, `invalid`, or `not-planned` label.

The **Verify-Issue-Closure** workflow will automatically reopen any issue closed without evidence. Do not work around it.

When implementing an issue:
- Write or update tests FIRST (TDD: red → green → refactor)
- Add Design-by-Contract preconditions/postconditions where it clarifies invariants
- Respect Law of Demeter — don’t reach through three layers
- Don’t duplicate code (DRY)
- Run tests locally before pushing
- If you can’t fully implement, leave the issue open and post a status comment

### How to close issues properly

| Method | Example |
|--------|---------|
| Closing keyword in PR body | `Closes #1234` or `Fixes #5678` |
| Closing keyword in PR title | `fix: resolve login crash (#1234)` |
| Exempt label | Apply `wontfix`, `roadmap`, `duplicate`, `invalid`, or `not-planned` |
| Bot + auto-generated label | Only for auto-generated issues closed by bots |

The workflow checks the PR timeline for cross-referenced merged PRs with closing keywords. If none are found and no exempt label is present, the issue is reopened with an explanatory comment.

---

<!-- BEGIN FLEET-MANAGED: repo-context-codemap -->

## 🧭 Repo Context & Codemap Freshness

> This section is managed centrally by Repository_Management and synced fleet-wide.
> Do NOT edit it directly in individual repositories — edit the source in Repository_Management/AGENTS.md.

Use repo-local context before broad exploration:

- Read `AGENTS.md` first, then check `docs/codemap.md` or `docs/operations/codemap_freshness_runbook.md` when present.
- If `.codemap/` exists, treat it as a generated local cache for navigation; verify important claims against source files before editing.
- If `.codemap/` is missing or stale, use source search (`rg`), focused file reads, and tests as the fallback. Report the missing/stale index as a rollout gap instead of blocking unrelated work.
- Do not commit `.codemap/` or `.codemap/index.db`. Codemap indexes are cache/artifact data and must stay ignored.
- To audit local fleet posture, run `python -m scripts.codemap_context_inventory --root .. --format markdown` from `Repository_Management`. This is a local, network-free inventory; it is not a substitute for repo-specific validation.

<!-- END FLEET-MANAGED: repo-context-codemap -->

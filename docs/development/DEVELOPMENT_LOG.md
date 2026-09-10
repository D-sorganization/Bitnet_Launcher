# Development Log — Bitnet_Launcher

State table for every feature in flight in this repository. Update
entries **in place**; never append dated sections. One entry per
feature, from proposal to ship. See the `development-logs` section of
`AGENTS.md` for the binding rules and
`shared_scripts/development_log.py` for the validator.

- **Portfolio:** personal
- **WIP limit:** 2
- **Last audited:** 2026-08-28 by bootstrap

## States

`proposed` → `in_progress` → `in_review` → `shipped`, with `parked`
reachable from any live state and `abandoned` from `parked`.
`shipped` never returns to `in_progress`; open a new entry instead.

## Active

### DL-#1596 · Maintainable Mermaid C4 Architecture Maps

- **State:** in_progress
- **Owner:** local
- **Issue:** #1596
- **Branch:** docs/1596-c4-architecture-map
- **PR:** not created
- **Paths:** docs/architecture/C4.md, scripts/architecture_map_contract.py, tests/test_architecture_map_contract.py, .github/workflows/architecture-map-contract.yml, AGENTS.md, README.md, SPEC.md
- **Started:** 2026-09-10
- **Last verified:** 2026-09-10 (C4.md validated, contract tests 4/4 pass)
- **Summary:** Baseline adoption of maintainable Mermaid C4 architecture maps in Bitnet_Launcher.
- **Next step:** Open PR, enable auto-merge, verify CI passes green.

### DL-0001 · Automation Bitnet Pr114 115

- **State:** parked
- **Owner:** unassigned
- **PR:** not created
- **Paths:** `.` — scope not yet narrowed; set real globs when
  this entry is reactivated.
- **Started:** 2026-08-28
- **Last verified:** 2026-08-28 (`d645b3d`)
- **Summary:** Seeded from local branch `automation/bitnet-pr114-115`, which is
  3 commit(s) ahead of the default branch with no
  development-log entry.
- **Parked:** 2026-08-28 — seeded during fleet rollout. Assign a
  governing issue and set `Paths` before moving this to a live
  state; a live entry without a real issue is orphaned by
  definition.

### DL-0002 · Fix Jules Case Collision

- **State:** parked
- **Owner:** unassigned
- **PR:** not created
- **Paths:** `.` — scope not yet narrowed; set real globs when
  this entry is reactivated.
- **Started:** 2026-08-28
- **Last verified:** 2026-08-28 (`859cdfd`)
- **Summary:** Seeded from local branch `fix/jules-case-collision`, which is
  1 commit(s) ahead of the default branch with no
  development-log entry.
- **Parked:** 2026-08-28 — seeded during fleet rollout. Assign a
  governing issue and set `Paths` before moving this to a live
  state; a live entry without a real issue is orphaned by
  definition.

## Shipped (Last 90 Days)

Entries stay here for 90 days after merge, then move to the archive.

## Archive

Older entries live in `DEVELOPMENT_LOG_ARCHIVE_<year>.md`.

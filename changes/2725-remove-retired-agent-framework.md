---
issue: 2725
summary: "Remove the retired vendored GAAI framework tree"
dl_state: "in_review"
next_step: "Independent exact-head review; not armed"
owner: "claude-og"
branch: "claude-og/2725-remove-gaai"
paths: ".gaai, tests/unit/test_gaai_removed_2725.py"
---

Deleted the checked-in `.gaai/` tree (GAAI is retired fleet-wide, Repository_Management#2725) and added a guard test that fails if the tree, a GAAI launcher script, or a GAAI pointer in a live entry point returns. Git history is the archive; the last commit containing the tree is cfb809f.

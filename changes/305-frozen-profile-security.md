---
issue: 305
summary: "Repair frozen dev and hub security dependencies"
dl_state: "in_review"
next_step: "Root review and serialized CI admission; no PR or push yet"
owner: "codex"
branch: "fix/certifi-ca-bundle-305"
paths: "uv.lock"
---

Expanded issue #305 to the minimal seven-package security closure. The frozen-profile audit changed from 14 unique advisories to zero; the 54-pin marker-union audit also found none. All 287 headless application tests passed on one CPU with the exact candidate overlay and the qualified existing base. Base library differences are recorded; this does not establish frozen Linux CI qualification. No workflow or application source changed. Evidence is retained in the fleet24 runtime. Keep unpublished until root admission.

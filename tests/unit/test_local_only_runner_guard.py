"""Regression tests for the local-only runner guard workflow contract."""

from __future__ import annotations

import ast
import contextlib
import io
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
GUARD_WORKFLOW = ROOT / ".github" / "workflows" / "local-only-runner-guard.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci-standard.yml"


def _workflow(path: Path) -> dict[str, Any]:
    parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict)
    return parsed


def _guard_script() -> str:
    job = _workflow(GUARD_WORKFLOW)["jobs"]["reject-hosted-runner-routing"]
    return job["steps"][-1]["run"]


def _expression_candidates() -> Callable[[str], list[str]]:
    """Load the implementation from the embedded workflow Python source."""
    tree = ast.parse(_guard_script())
    nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.FunctionDef))
        and (
            isinstance(node, ast.FunctionDef)
            and node.name == "expression_candidates"
            or isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "QUOTED_LITERAL"
                for target in node.targets
            )
        )
    ]
    namespace: dict[str, Any] = {"re": re}
    exec(
        compile(ast.Module(body=nodes, type_ignores=[]), str(GUARD_WORKFLOW), "exec"),
        namespace,
    )
    return namespace["expression_candidates"]


def _run_guard(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    visibility: str,
    workflow_text: str | dict[str, str],
) -> tuple[int, str]:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    fixtures = (
        {"candidate.yml": workflow_text}
        if isinstance(workflow_text, str)
        else workflow_text
    )
    for name, text in fixtures.items():
        (workflows / name).write_text(text, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REPO_VISIBILITY", visibility)
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(
                compile(_guard_script(), str(GUARD_WORKFLOW), "exec"),
                {"__name__": "__main__"},
            )
    except SystemExit as exc:
        return int(exc.code or 0), output.getvalue()
    return 0, output.getvalue()


def test_pull_request_guard_runs_without_path_filter_and_when_ready() -> None:
    events = _workflow(GUARD_WORKFLOW)["on"]
    pull_request = events["pull_request"]

    assert "paths" not in pull_request
    assert {"opened", "synchronize", "reopened", "ready_for_review"}.issubset(
        set(pull_request["types"])
    )
    job = _workflow(GUARD_WORKFLOW)["jobs"]["reject-hosted-runner-routing"]
    assert job["name"] == "Reject hosted runner routing"
    assert job["runs-on"] == "ubuntu-latest"


def test_ci_standard_keeps_real_quality_gate_without_duplicate_guard_job() -> None:
    jobs = _workflow(CI_WORKFLOW)["jobs"]

    assert "local-only-workflows" not in jobs
    assert all(
        job.get("name") != "Reject hosted runner routing" for job in jobs.values()
    )
    assert not any(
        step.get("name") == "Dummy"
        for job in jobs.values()
        for step in job.get("steps", [])
    )
    assert {"lint", "tests", "quality-gate"}.issubset(jobs)
    assert set(jobs["quality-gate"]["needs"]) == {"lint", "tests"}
    assert jobs["quality-gate"]["if"] == "always()"


def test_required_check_producers_run_in_merge_queue() -> None:
    """Required checks must report on merge_group (Repository_Management#1890)."""
    for workflow in (GUARD_WORKFLOW, CI_WORKFLOW):
        assert "merge_group" in _workflow(workflow)["on"]


def test_embedded_python_has_no_unmatched_actions_expression_opener() -> None:
    assert "${{" not in _guard_script()


def test_expression_candidates_preserve_plain_and_quoted_alternatives() -> None:
    candidates = _expression_candidates()

    assert candidates("d-sorg-fleet") == []
    expression = (
        "$" + "{{ vars.RUNNER_TARGET == 'local' && 'd-sorg-fleet' || 'ubuntu-latest' }}"
    )
    assert candidates(expression) == ["local", "d-sorg-fleet", "ubuntu-latest"]


@pytest.mark.parametrize("visibility", ["private", "internal"])
def test_private_and_internal_reject_hosted_expression_alternative(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, visibility: str
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        visibility,
        """name: Candidate
jobs:
  build:
    runs-on: "${{ vars.RUNNER_TARGET == 'local' && 'd-sorg-fleet' || 'ubuntu-latest' }}"
""",
    )

    assert code == 1
    assert "ubuntu-latest" in output
    assert "::error::" in output


def test_public_hosted_runner_is_allowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        "public",
        "name: Candidate\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    )

    assert code == 0
    assert "::error::" not in output
    assert "hosted runners permitted" in output


def test_public_self_hosted_route_is_advisory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        "public",
        "name: Candidate\njobs:\n  build:\n    runs-on: d-sorg-fleet\n",
    )

    assert code == 0
    assert "::warning::" in output
    assert "fork PR can run untrusted code" in output


def test_dynamic_needs_output_is_resolved_before_visibility_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        "private",
        """name: Candidate
jobs:
  picker:
    name: Reject hosted runner routing
    runs-on: ubuntu-latest
    steps:
      - run: |
          runner=$RUNNER
          echo 'runner=ubuntu-latest'
          echo 'runner=d-sorg-fleet'
  build:
    needs: [picker]
    runs-on: ${{ needs.picker.outputs.runner }}
""",
    )

    assert code == 1
    assert "candidate.yml::build" in output
    assert "ubuntu-latest" in output


def test_visibility_aware_needs_output_remains_trusted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        "private",
        """name: Candidate
jobs:
  picker:
    name: Reject hosted runner routing
    runs-on: ubuntu-latest
    steps:
      - run: echo repository.visibility
  build:
    needs: [picker]
    runs-on: ${{ needs.picker.outputs.runner }}
""",
    )

    assert code == 0
    assert "visibility-aware picker" in output
    assert "::error::" not in output


def test_guard_file_and_job_allowlists_remain_effective(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code, output = _run_guard(
        monkeypatch,
        tmp_path,
        "private",
        {
            "runner-health-alert.yml": """name: Alert
jobs:
  check:
    runs-on: ubuntu-latest
""",
            "candidate.yml": """name: Candidate
jobs:
  coordination:
    name: Local-Only Workflow Runner Guard
    runs-on: ubuntu-latest
""",
        },
    )

    assert code == 0
    assert "::error::" not in output

"""The vendored GAAI framework is gone and must not come back.

The owner retired GAAI fleet-wide (Repository_Management#2725). The checked-in
``.gaai/`` tree is removed; these checks keep it, any GAAI launcher script, and
live pointers to it from returning.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]

# Entry points an agent or tool reads on every run. A GAAI pointer here would
# send it to files that no longer exist.
LIVE_ENTRY_POINTS = (
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    ".gitignore",
)

_GAAI = re.compile(r"gaai", re.IGNORECASE)


def test_vendored_tree_is_removed() -> None:
    assert not (REPO_ROOT / ".gaai").exists()


def _tracked_files() -> list[str]:
    """Paths git tracks; build output such as ``__pycache__`` never counts."""
    return subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()


def test_no_gaai_launcher_script_exists() -> None:
    this_file = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()
    found = [
        path
        for path in _tracked_files()
        if _GAAI.search(Path(path).name) and path != this_file
    ]
    assert found == []


@pytest.mark.parametrize("relative_path", LIVE_ENTRY_POINTS)
def test_live_entry_point_does_not_mention_gaai(relative_path: str) -> None:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path} moved -- update LIVE_ENTRY_POINTS"
    hits = [
        f"{relative_path}:{number}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _GAAI.search(line)
    ]
    assert hits == []

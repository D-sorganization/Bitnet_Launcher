import os
from pathlib import Path
from typing import Any

import pytest


def setup_mock_models(base_dir: Path, n_models: int = 100, n_files: int = 10) -> None:
    for i in range(n_models):
        model_dir = base_dir / f"model_family_{i}"
        model_dir.mkdir(parents=True, exist_ok=True)
        for j in range(n_files):
            ext = ".gguf" if j == 0 else ".txt"
            (model_dir / f"file_{j}{ext}").write_text("dummy data")


def run_iterdir(models_dir: Path) -> int:
    found = []
    for model_dir in sorted(models_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        candidates = sorted(list(model_dir.glob("*.gguf")))
        if candidates:
            chosen = candidates[0]
            size = chosen.stat().st_size
            found.append((model_dir.name, chosen, size))
    return len(found)


def run_scandir(models_dir: Path) -> int:
    found = []
    for model_entry in sorted(os.scandir(models_dir), key=lambda e: e.name):
        if not model_entry.is_dir():
            continue
        candidates = []
        for file_entry in os.scandir(model_entry.path):
            if file_entry.name.lower().endswith(".gguf") and file_entry.is_file():
                candidates.append(file_entry)
        if candidates:
            candidates.sort(key=lambda e: e.name)
            chosen = candidates[0]
            size = chosen.stat().st_size
            found.append((model_entry.name, Path(chosen.path), size))
    return len(found)


@pytest.mark.benchmark(group="model_discovery")
def test_bench_iterdir(benchmark: Any, tmp_path: Path) -> None:
    setup_mock_models(tmp_path, 100, 10)
    count = benchmark(run_iterdir, tmp_path)
    assert count == 100


@pytest.mark.benchmark(group="model_discovery")
def test_bench_scandir(benchmark: Any, tmp_path: Path) -> None:
    setup_mock_models(tmp_path, 100, 10)
    count = benchmark(run_scandir, tmp_path)
    assert count == 100

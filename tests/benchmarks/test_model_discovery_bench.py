from pathlib import Path
from typing import Any

import pytest

from bitnet_launcher.models import discover_models


def setup_realistic_models(base_dir: Path, n_models: int = 50) -> None:
    for i in range(n_models):
        model_dir = base_dir / f"bitnet-model-{i}"
        model_dir.mkdir(parents=True, exist_ok=True)
        # Add some stray files
        (model_dir / "README.md").write_text("info")
        (model_dir / "config.json").write_text("{}")
        # Add a placeholder GGUF
        (model_dir / "metadata.gguf").write_bytes(b"\x00" * 1000)
        # Add the real GGUF
        (model_dir / f"model-i2_s-{i}.gguf").write_bytes(b"\x00" * 2_000_000)
        # Add an alternative GGUF
        (model_dir / f"model-q4_k_m-{i}.gguf").write_bytes(b"\x00" * 3_000_000)


@pytest.mark.benchmark(group="model_discovery")
def test_bench_discover_models_50(benchmark: Any, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    setup_realistic_models(models_dir, 50)

    result = benchmark(discover_models, models_dir)
    assert len(result) == 50

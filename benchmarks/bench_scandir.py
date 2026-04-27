import os
import tempfile
import time
from pathlib import Path


def setup_mock_models(base_dir: Path, n_models: int = 100, n_files: int = 10):
    for i in range(n_models):
        model_dir = base_dir / f"model_family_{i}"
        model_dir.mkdir(parents=True, exist_ok=True)
        for j in range(n_files):
            ext = ".gguf" if j == 0 else ".txt"
            (model_dir / f"file_{j}{ext}").write_text("dummy data")


def bench_iterdir(models_dir: Path):
    start = time.perf_counter()
    found = []
    for model_dir in sorted(models_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        candidates = sorted(list(model_dir.glob("*.gguf")))
        if candidates:
            chosen = candidates[0]
            size = chosen.stat().st_size
            found.append((model_dir.name, chosen, size))
    return time.perf_counter() - start, len(found)


def bench_scandir(models_dir: Path):
    start = time.perf_counter()
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
    return time.perf_counter() - start, len(found)


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Setting up 100 mock models in {tmp_path}...")  # noqa: T201
        setup_mock_models(tmp_path, 100, 10)

        # Warm up
        bench_iterdir(tmp_path)
        bench_scandir(tmp_path)

        it_time, it_count = bench_iterdir(tmp_path)
        sc_time, sc_count = bench_scandir(tmp_path)

        print(f"Path.iterdir() + glob: {it_time:.6f}s ({it_count} models)")  # noqa: T201
        print(f"os.scandir():           {sc_time:.6f}s ({sc_count} models)")  # noqa: T201
        print(f"Speedup: {it_time / sc_time:.2f}x")  # noqa: T201


if __name__ == "__main__":
    main()

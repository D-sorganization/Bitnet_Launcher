"""Unit tests for bitnet_launcher.models.

All tests use ``tmp_path`` fixtures — no real BitNet installation needed.
All tests are headless-safe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bitnet_launcher.models import (
    ModelInfo,
    _fmt_bytes,
    discover_models,
)

# ── _fmt_bytes ─────────────────────────────────────────────────────────────────


class TestFmtBytes:
    def test_bytes(self) -> None:
        assert _fmt_bytes(500) == "500 B"

    def test_kilobytes(self) -> None:
        assert _fmt_bytes(2048) == "2 KB"

    def test_megabytes(self) -> None:
        assert _fmt_bytes(1024 * 1024) == "1 MB"

    def test_gigabytes(self) -> None:
        result = _fmt_bytes(2 * 1024 * 1024 * 1024)
        assert "GB" in result

    def test_zero(self) -> None:
        assert _fmt_bytes(0) == "0 B"


# ── ModelInfo ──────────────────────────────────────────────────────────────────


class TestModelInfo:
    def test_display_name_includes_size(self, tmp_path: Path) -> None:
        gguf = tmp_path / "model.gguf"
        gguf.touch()
        info = ModelInfo(name="my-model", path=gguf, size_bytes=1024)
        assert "my-model" in info.display_name
        assert "KB" in info.display_name or "B" in info.display_name

    def test_immutable(self, tmp_path: Path) -> None:
        from dataclasses import FrozenInstanceError

        gguf = tmp_path / "model.gguf"
        gguf.touch()
        info = ModelInfo(name="m", path=gguf, size_bytes=0)
        with pytest.raises(FrozenInstanceError):
            info.name = "other"  # type: ignore[misc]

    def test_name_blank_raises(self, tmp_path: Path) -> None:
        gguf = tmp_path / "model.gguf"
        gguf.touch()
        with pytest.raises(ValueError, match="name must not be blank"):
            ModelInfo(name="   ", path=gguf, size_bytes=0)

    def test_path_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="path must be a Path"):
            ModelInfo(name="m", path="/bad", size_bytes=0)  # type: ignore[arg-type]

    def test_size_bytes_wrong_type(self, tmp_path: Path) -> None:
        gguf = tmp_path / "model.gguf"
        gguf.touch()
        with pytest.raises(TypeError, match="size_bytes must be int"):
            ModelInfo(name="m", path=gguf, size_bytes=1.0)  # type: ignore[arg-type]

    def test_size_bytes_negative(self, tmp_path: Path) -> None:
        gguf = tmp_path / "model.gguf"
        gguf.touch()
        with pytest.raises(ValueError, match="size_bytes must be >= 0"):
            ModelInfo(name="m", path=gguf, size_bytes=-1)


# ── discover_models ────────────────────────────────────────────────────────────


def _make_model_dir(
    parent: Path,
    name: str,
    size: int = 2_000_000,
    filename: str = "model.gguf",
) -> Path:
    """Create a model directory with a stub .gguf file of the given size."""
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    gguf = d / filename
    gguf.write_bytes(b"\x00" * size)
    return d


class TestDiscoverModels:
    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        result = discover_models(tmp_path / "nonexistent")
        assert result == []

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        result = discover_models(models_dir)
        assert result == []

    def test_single_model_discovered(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        _make_model_dir(models_dir, "llama3-1b")
        result = discover_models(models_dir)
        assert len(result) == 1
        assert result[0].name == "llama3-1b"

    def test_prefers_i2_s_file(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        d = models_dir / "llama3-1b"
        d.mkdir()
        other = d / "model-other.gguf"
        i2s = d / "model-i2_s.gguf"
        other.write_bytes(b"\x00" * 2_000_000)
        i2s.write_bytes(b"\x00" * 3_000_000)
        result = discover_models(models_dir)
        assert result[0].path.name == "model-i2_s.gguf"

    def test_accepts_mixed_case_gguf_suffix(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        _make_model_dir(models_dir, "llama3-1b", filename="MODEL.GGUF")
        result = discover_models(models_dir)
        assert len(result) == 1
        assert result[0].path.name == "MODEL.GGUF"

    def test_skips_placeholder_files(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        d = models_dir / "tiny-model"
        d.mkdir()
        tiny = d / "placeholder.gguf"
        tiny.write_bytes(b"\x00" * 100)  # below MIN_MODEL_BYTES
        result = discover_models(models_dir)
        assert result == []

    def test_multiple_models_sorted(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        _make_model_dir(models_dir, "zzz-model")
        _make_model_dir(models_dir, "aaa-model")
        result = discover_models(models_dir)
        assert [m.name for m in result] == ["aaa-model", "zzz-model"]

    def test_ignores_non_dir_entries(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        (models_dir / "stray-file.txt").write_text("hello")
        result = discover_models(models_dir)
        assert result == []

    def test_dir_without_gguf_skipped(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        d = models_dir / "no-weights"
        d.mkdir()
        (d / "README.md").write_text("hi")
        result = discover_models(models_dir)
        assert result == []

    def test_models_dir_wrong_type_raises(self) -> None:
        with pytest.raises(TypeError, match="models_dir must be a Path"):
            discover_models("/not/a/path")  # type: ignore[arg-type]

    def test_models_dir_is_file_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(ValueError, match="not a directory"):
            discover_models(f)

    def test_size_bytes_correct(self, tmp_path: Path) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        _make_model_dir(models_dir, "sized-model", size=5_000_000)
        result = discover_models(models_dir)
        assert result[0].size_bytes == 5_000_000

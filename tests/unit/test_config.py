"""Unit tests for bitnet_launcher.config.

All tests are headless-safe (no Qt dependency).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from bitnet_launcher.config import BitnetConfig, InferenceConfig

# ── InferenceConfig defaults ───────────────────────────────────────────────────


class TestInferenceConfigDefaults:
    def test_threads_default(self) -> None:
        cfg = InferenceConfig()
        assert cfg.threads == 4

    def test_ctx_size_default(self) -> None:
        cfg = InferenceConfig()
        assert cfg.ctx_size == 2048

    def test_temperature_default(self) -> None:
        cfg = InferenceConfig()
        assert cfg.temperature == pytest.approx(0.8)

    def test_n_predict_default(self) -> None:
        cfg = InferenceConfig()
        assert cfg.n_predict == -1

    def test_system_prompt_default(self) -> None:
        cfg = InferenceConfig()
        assert cfg.system_prompt == "You are a helpful assistant."


# ── InferenceConfig valid edge cases ──────────────────────────────────────────


class TestInferenceConfigValid:
    def test_threads_minimum(self) -> None:
        cfg = InferenceConfig(threads=1)
        assert cfg.threads == 1

    def test_ctx_size_minimum(self) -> None:
        cfg = InferenceConfig(ctx_size=512)
        assert cfg.ctx_size == 512

    def test_temperature_zero(self) -> None:
        cfg = InferenceConfig(temperature=0.0)
        assert cfg.temperature == pytest.approx(0.0)

    def test_temperature_max(self) -> None:
        cfg = InferenceConfig(temperature=2.0)
        assert cfg.temperature == pytest.approx(2.0)

    def test_n_predict_unlimited(self) -> None:
        cfg = InferenceConfig(n_predict=-1)
        assert cfg.n_predict == -1

    def test_n_predict_positive(self) -> None:
        cfg = InferenceConfig(n_predict=256)
        assert cfg.n_predict == 256

    def test_temperature_accepts_int(self) -> None:
        """temperature accepts int (subtype of numeric)."""
        cfg = InferenceConfig(temperature=1)
        assert cfg.temperature == pytest.approx(1.0)


# ── InferenceConfig DbC: TypeError ────────────────────────────────────────────


class TestInferenceConfigTypeErrors:
    def test_threads_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="threads must be int"):
            InferenceConfig(threads="4")  # type: ignore[arg-type]

    def test_ctx_size_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="ctx_size must be int"):
            InferenceConfig(ctx_size=2048.0)  # type: ignore[arg-type]

    def test_temperature_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="temperature must be numeric"):
            InferenceConfig(temperature="0.8")  # type: ignore[arg-type]

    def test_n_predict_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="n_predict must be int"):
            InferenceConfig(n_predict=1.5)  # type: ignore[arg-type]

    def test_system_prompt_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="system_prompt must be str"):
            InferenceConfig(system_prompt=42)  # type: ignore[arg-type]


# ── InferenceConfig DbC: ValueError ───────────────────────────────────────────


class TestInferenceConfigValueErrors:
    def test_threads_zero(self) -> None:
        with pytest.raises(ValueError, match="threads must be >= 1"):
            InferenceConfig(threads=0)

    def test_threads_negative(self) -> None:
        with pytest.raises(ValueError, match="threads must be >= 1"):
            InferenceConfig(threads=-1)

    def test_ctx_size_too_small(self) -> None:
        with pytest.raises(ValueError, match="ctx_size must be >= 512"):
            InferenceConfig(ctx_size=256)

    def test_temperature_below_zero(self) -> None:
        with pytest.raises(ValueError, match="temperature must be in"):
            InferenceConfig(temperature=-0.1)

    def test_temperature_above_two(self) -> None:
        with pytest.raises(ValueError, match="temperature must be in"):
            InferenceConfig(temperature=2.1)

    def test_n_predict_too_small(self) -> None:
        with pytest.raises(ValueError, match="n_predict must be >= -1"):
            InferenceConfig(n_predict=-2)

    def test_system_prompt_blank(self) -> None:
        with pytest.raises(ValueError, match="system_prompt must not be blank"):
            InferenceConfig(system_prompt="   ")


# ── BitnetConfig ───────────────────────────────────────────────────────────────


class TestBitnetConfig:
    def test_defaults_are_paths(self) -> None:
        cfg = BitnetConfig()
        assert isinstance(cfg.bitnet_root, Path)
        assert isinstance(cfg.llama_cli, Path)
        assert isinstance(cfg.models_dir, Path)

    def test_wt_exe_default_non_blank(self) -> None:
        cfg = BitnetConfig()
        assert cfg.wt_exe.strip()

    def test_custom_paths(self, tmp_path: Path) -> None:
        cfg = BitnetConfig(
            bitnet_root=tmp_path,
            llama_cli=tmp_path / "llama-cli",
            models_dir=tmp_path / "models",
            wt_exe="wt.exe",
        )
        assert cfg.bitnet_root == tmp_path

    def test_bitnet_root_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="bitnet_root must be a Path"):
            BitnetConfig(bitnet_root="/not/a/path")  # type: ignore[arg-type]

    def test_llama_cli_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="llama_cli must be a Path"):
            BitnetConfig(llama_cli="/not/a/path")  # type: ignore[arg-type]

    def test_models_dir_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="models_dir must be a Path"):
            BitnetConfig(models_dir="/not/a/path")  # type: ignore[arg-type]

    def test_wt_exe_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="wt_exe must be a str"):
            BitnetConfig(wt_exe=123)  # type: ignore[arg-type]

    def test_wt_exe_blank(self) -> None:
        with pytest.raises(ValueError, match="wt_exe must not be blank"):
            BitnetConfig(wt_exe="   ")

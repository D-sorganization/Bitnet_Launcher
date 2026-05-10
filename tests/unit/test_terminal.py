"""Unit tests for bitnet_launcher.terminal.

Tests cover build_command() output; launch_terminal() is tested only for
type/value validation since it calls subprocess.Popen which we mock.
All tests are headless-safe.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bitnet_launcher.config import InferenceConfig
from bitnet_launcher.models import ModelInfo
from bitnet_launcher.terminal import build_command, launch_terminal

# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def llama_cli(tmp_path: Path) -> Path:
    cli = tmp_path / "llama-cli"
    cli.touch()
    return cli


@pytest.fixture()
def model(tmp_path: Path) -> ModelInfo:
    gguf = tmp_path / "model.gguf"
    gguf.write_bytes(b"\x00" * 2_000_000)
    return ModelInfo(name="test-model", path=gguf, size_bytes=2_000_000)


@pytest.fixture()
def config() -> InferenceConfig:
    return InferenceConfig(
        threads=4,
        ctx_size=2048,
        temperature=0.8,
        n_predict=-1,
        system_prompt="You are a helpful assistant.",
    )


# ── build_command ──────────────────────────────────────────────────────────────


class TestBuildCommand:
    def test_returns_list_of_strings(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert isinstance(cmd, list)
        assert all(isinstance(x, str) for x in cmd)

    def test_first_element_is_cli_path(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert cmd[0] == str(llama_cli)

    def test_model_path_included(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == str(model.path)

    def test_threads_included(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-t" in cmd
        idx = cmd.index("-t")
        assert cmd[idx + 1] == str(config.threads)

    def test_ctx_size_included(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-c" in cmd
        idx = cmd.index("-c")
        assert cmd[idx + 1] == str(config.ctx_size)

    def test_temperature_included(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "--temp" in cmd

    def test_n_predict_minus_one_omitted(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        """n_predict == -1 means unlimited; -n flag must be absent."""
        assert config.n_predict == -1
        cmd = build_command(llama_cli, model, config)
        assert "-n" not in cmd

    def test_n_predict_positive_included(
        self, llama_cli: Path, model: ModelInfo
    ) -> None:
        cfg = InferenceConfig(n_predict=256)
        cmd = build_command(llama_cli, model, cfg)
        assert "-n" in cmd
        idx = cmd.index("-n")
        assert cmd[idx + 1] == "256"

    def test_conversation_mode_flag(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-cnv" in cmd

    def test_system_prompt_included(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-p" in cmd
        idx = cmd.index("-p")
        assert cmd[idx + 1] == config.system_prompt

    def test_batch_size_one(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        cmd = build_command(llama_cli, model, config)
        assert "-b" in cmd
        idx = cmd.index("-b")
        assert cmd[idx + 1] == "1"

    def test_ngl_zero(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        """GPU layers must be 0 (BitNet is CPU-only)."""
        cmd = build_command(llama_cli, model, config)
        assert "-ngl" in cmd
        idx = cmd.index("-ngl")
        assert cmd[idx + 1] == "0"


# ── build_command: DbC ────────────────────────────────────────────────────────


class TestBuildCommandTypeErrors:
    def test_llama_cli_wrong_type(
        self, model: ModelInfo, config: InferenceConfig
    ) -> None:
        with pytest.raises(TypeError, match="llama_cli must be a Path"):
            build_command("/bin/llama-cli", model, config)  # type: ignore[arg-type]

    def test_model_wrong_type(self, llama_cli: Path, config: InferenceConfig) -> None:
        with pytest.raises(TypeError, match="model must be a ModelInfo"):
            build_command(llama_cli, "not-a-model", config)  # type: ignore[arg-type]

    def test_config_wrong_type(self, llama_cli: Path, model: ModelInfo) -> None:
        with pytest.raises(TypeError, match="config must be an InferenceConfig"):
            build_command(llama_cli, model, {"threads": 4})  # type: ignore[arg-type]


# ── launch_terminal: DbC ──────────────────────────────────────────────────────


class TestLaunchTerminalTypeErrors:
    def test_wt_exe_blank_raises(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig, tmp_path: Path
    ) -> None:
        with pytest.raises(ValueError, match="wt_exe must not be blank"):
            launch_terminal(llama_cli, model, config, tmp_path, "   ")

    def test_bitnet_root_wrong_type(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig
    ) -> None:
        with pytest.raises(TypeError, match="bitnet_root must be a Path"):
            launch_terminal(llama_cli, model, config, "/tmp", "wt.exe")  # type: ignore[arg-type]

    def test_wt_exe_wrong_type(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig, tmp_path: Path
    ) -> None:
        with pytest.raises(TypeError, match="wt_exe must be a str"):
            launch_terminal(llama_cli, model, config, tmp_path, 42)  # type: ignore[arg-type]


# ── launch_terminal: subprocess call ─────────────────────────────────────────


class TestLaunchTerminalPopen:
    def test_popen_called_with_wt(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig, tmp_path: Path
    ) -> None:
        with patch("bitnet_launcher.terminal.subprocess.Popen") as mock_popen:
            launch_terminal(llama_cli, model, config, tmp_path, "/fake/wt.exe")
            mock_popen.assert_called_once()
            args = mock_popen.call_args.args[0]
            assert args[0] == "/fake/wt.exe"
            assert "new-tab" in args

    def test_fallback_to_wt_exe_on_file_not_found(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig, tmp_path: Path
    ) -> None:
        call_count = 0

        def fake_popen(argv: list[str], **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if argv[0] != "wt.exe":
                raise FileNotFoundError("not found")
            return MagicMock()

        with patch("bitnet_launcher.terminal.subprocess.Popen", side_effect=fake_popen):
            launch_terminal(llama_cli, model, config, tmp_path, "/missing/wt.exe")

        assert call_count == 2

    def test_model_name_in_title(
        self, llama_cli: Path, model: ModelInfo, config: InferenceConfig, tmp_path: Path
    ) -> None:
        with patch("bitnet_launcher.terminal.subprocess.Popen") as mock_popen:
            launch_terminal(llama_cli, model, config, tmp_path, "wt.exe")
            args = mock_popen.call_args.args[0]
            title_idx = args.index("--title") + 1
            assert model.name in args[title_idx]

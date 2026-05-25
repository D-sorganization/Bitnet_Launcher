"""Tests for bitnet_launcher.hub — catalog and download_model DbC."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from bitnet_launcher.hub import CATALOG, HubModel, download_model


def test_catalog_non_empty() -> None:
    assert len(CATALOG) >= 16


def test_catalog_entries_valid() -> None:
    for m in CATALOG:
        assert m.repo_id
        assert m.name
        assert m.params
        assert m.size_gb > 0
        assert isinstance(m.tags, list)


def test_hub_model_frozen() -> None:
    m: HubModel = CATALOG[0]
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        m.name = "changed"  # type: ignore[misc]


def test_download_model_type_error_hub_model() -> None:
    with pytest.raises(TypeError):
        download_model(
            "not_a_hub_model",  # type: ignore[arg-type]
            Path("/tmp"),
            Path("/tmp"),
            lambda x: None,
            lambda x: None,
        )


def test_download_model_type_error_models_dir() -> None:
    with pytest.raises(TypeError):
        download_model(
            CATALOG[0],
            "/tmp",  # type: ignore[arg-type]
            Path("/tmp"),
            lambda x: None,
            lambda x: None,
        )


def test_download_model_type_error_bitnet_root() -> None:
    with pytest.raises(TypeError):
        download_model(
            CATALOG[0],
            Path("/tmp"),
            "/tmp",  # type: ignore[arg-type]
            lambda x: None,
            lambda x: None,
        )


def test_catalog_all_repo_ids_unique() -> None:
    repo_ids = [m.repo_id for m in CATALOG]
    assert len(repo_ids) == len(set(repo_ids)), "Duplicate repo_id found in CATALOG"


def test_catalog_microsoft_model_present() -> None:
    names = [m.repo_id for m in CATALOG]
    assert "microsoft/BitNet-b1.58-2B-4T" in names


def test_hub_model_tags_are_strings() -> None:
    for m in CATALOG:
        for tag in m.tags:
            assert isinstance(tag, str), f"Non-string tag in {m.name}: {tag!r}"


def test_hub_model_gguf_file_defaults_none() -> None:
    assert CATALOG[0].gguf_file is None


def test_hub_model_blank_gguf_file_rejected() -> None:
    with pytest.raises(ValueError):
        HubModel("r", "n", "d", "1B", 1.0, [], gguf_file="   ")


def test_bitcpm_entries_are_prebuilt_gguf() -> None:
    bitcpm = [m for m in CATALOG if "BitCPM4" in m.repo_id]
    assert len(bitcpm) == 3, "expected 1B/3B/8B BitCPM4 entries"
    for m in bitcpm:
        assert m.repo_id.endswith("-gguf"), m.repo_id
        assert m.gguf_file and m.gguf_file.endswith(".gguf"), m.gguf_file


def test_download_model_dispatches_to_prebuilt(monkeypatch, tmp_path) -> None:
    """download_model must route gguf_file entries to the prebuilt path."""
    import bitnet_launcher.hub as hub

    seen: dict[str, str] = {}

    def fake_prebuilt(hub_model, models_dir, on_log, on_progress):  # type: ignore[no-untyped-def]
        seen["repo_id"] = hub_model.repo_id
        on_progress(1.0)
        return models_dir / hub_model.name

    monkeypatch.setattr(hub, "_download_prebuilt_gguf", fake_prebuilt)
    model = next(m for m in CATALOG if m.gguf_file is not None)

    out = hub.download_model(
        model, tmp_path, tmp_path, lambda _s: None, lambda _f: None
    )

    assert seen["repo_id"] == model.repo_id
    assert out == tmp_path / model.name

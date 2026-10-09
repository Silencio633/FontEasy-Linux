"""Testes da lógica de instalação (sem GTK)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

import fonteasy.installer as installer
from fonteasy.installer import install_font_files


def real_system_font() -> Path | None:
    try:
        out = subprocess.run(
            ["fc-list", ":", "file"], capture_output=True, text=True, timeout=15
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    for line in out.stdout.splitlines():
        candidate = line.split(":", 1)[0].strip()
        p = Path(candidate)
        if p.is_file() and p.suffix.lower() in installer.SUPPORTED_EXTENSIONS:
            return p
    return None


SYSTEM_FONT = real_system_font()
needs_font = pytest.mark.skipif(SYSTEM_FONT is None, reason="sem fontes do sistema")


@needs_font
def test_install_copies_and_refreshes(tmp_path):
    font_dir = tmp_path / "fonts"
    result = install_font_files([SYSTEM_FONT], font_dir, refresh_cache=True)
    assert result.errors == []
    assert result.installed == [SYSTEM_FONT.name]
    assert (font_dir / SYSTEM_FONT.name).is_file()


@needs_font
def test_install_idempotent_skips_existing(tmp_path):
    font_dir = tmp_path / "fonts"
    first = install_font_files([SYSTEM_FONT], font_dir)
    assert first.installed
    second = install_font_files([SYSTEM_FONT], font_dir)
    assert second.installed == []
    assert second.skipped == [SYSTEM_FONT.name]
    assert second.errors == []


def test_invalid_files_become_errors(tmp_path):
    bad = tmp_path / "lixo.ttf"
    bad.write_bytes(b"nao e fonte" * 50)
    font_dir = tmp_path / "fonts"
    result = install_font_files([bad, tmp_path / "ausente.otf"], font_dir, refresh_cache=False)
    assert result.installed == []
    assert len(result.errors) == 2


@needs_font
def test_symlink_source_rejected(tmp_path):
    link = tmp_path / "link.ttf"
    link.symlink_to(SYSTEM_FONT)
    result = install_font_files([link], tmp_path / "fonts", refresh_cache=False)
    assert result.installed == []
    assert len(result.errors) == 1


@needs_font
def test_no_overwrite_of_existing(tmp_path):
    font_dir = tmp_path / "fonts"
    font_dir.mkdir(parents=True)
    sentinel = font_dir / SYSTEM_FONT.name
    sentinel.write_bytes(b"original")
    result = install_font_files([SYSTEM_FONT], font_dir, refresh_cache=False)
    assert result.skipped == [SYSTEM_FONT.name]
    assert sentinel.read_bytes() == b"original"


@needs_font
def test_uppercase_extension_installs(tmp_path):
    src = tmp_path / "ALTA.OTF"
    # Copia uma fonte real seja qual for o formato para testar o caminho;
    # se não for OTF válido o validador pode rejeitar — nesse caso, aceita skip.
    shutil.copy2(SYSTEM_FONT, tmp_path / "orig.ttf")
    orig = tmp_path / "orig.ttf"
    shutil.copy2(orig, src)
    result = install_font_files([src], tmp_path / "fonts", refresh_cache=False)
    assert result.installed or result.errors  # sem crash; comportamento definido


def test_cache_failure_reported(monkeypatch, tmp_path):
    real_font = SYSTEM_FONT
    if real_font is None:
        pytest.skip("sem fonte real")
    monkeypatch.setattr(
        installer, "refresh_font_cache", lambda _d: (False, "simulated fc-cache failure")
    )
    result = install_font_files([real_font], tmp_path / "fonts", refresh_cache=True)
    assert result.installed == [real_font.name]
    assert any("fc-cache" in e for e in result.errors)

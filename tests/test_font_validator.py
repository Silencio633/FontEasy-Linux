"""Testes do validador de fontes (usa fontes reais do sistema)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

import fonteasy.font_validator as font_validator
from fonteasy.font_validator import SUPPORTED_EXTENSIONS

_test_font = font_validator.test_font


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
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            return p
    return None


SYSTEM_FONT = real_system_font()
needs_font = pytest.mark.skipif(SYSTEM_FONT is None, reason="sem fontes do sistema / fc-list ausente")


@needs_font
def test_valid_font_returns_family_style():
    ok, info = _test_font(SYSTEM_FONT)
    assert ok is True
    assert "—" in info or "|" not in info  # "Família — Estilo"


def test_unsupported_extension(tmp_path):
    f = tmp_path / "nota.txt"
    f.write_text("hello")
    ok, msg = _test_font(f)
    assert not ok
    assert "não suportado" in msg.lower() or "suportado" in msg.lower()


def test_missing_file(tmp_path):
    ok, msg = _test_font(tmp_path / "ausente.ttf")
    assert not ok
    assert "não existe" in msg.lower()


def test_symlink_rejected(tmp_path):
    if SYSTEM_FONT is None:
        pytest.skip("sem fonte real para ligar")
    link = tmp_path / "ligacao.ttf"
    link.symlink_to(SYSTEM_FONT)
    ok, msg = _test_font(link)
    assert not ok
    assert "simbólica" in msg.lower()


def test_empty_file_rejected(tmp_path):
    f = tmp_path / "vazia.ttf"
    f.write_bytes(b"")
    ok, msg = _test_font(f)
    assert not ok
    assert "vazio" in msg.lower()


def test_corrupt_file_rejected(tmp_path):
    f = tmp_path / "lixo.ttf"
    f.write_bytes(b"isto nao e uma fonte" * 100)
    ok, msg = _test_font(f)
    assert not ok
    assert "fontconfig" in msg.lower() or "analisar" in msg.lower()


def test_size_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(font_validator, "MAX_FILE_SIZE_BYTES", 10)
    f = tmp_path / "grande.ttf"
    f.write_bytes(b"x" * 11)
    ok, msg = _test_font(f)
    assert not ok
    assert "limite" in msg.lower()


@needs_font
def test_uppercase_extension(tmp_path):
    dest = tmp_path / "COPIA.TTF"
    shutil.copy2(SYSTEM_FONT, dest)
    ok, _ = _test_font(dest)
    assert ok is True

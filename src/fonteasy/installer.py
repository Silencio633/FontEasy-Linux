"""Lógica de instalação de fontes (sem dependência do GTK).

Separada da interface para ser testável com pytest e reutilizável.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from fonteasy.font_validator import SUPPORTED_EXTENSIONS, test_font


def get_default_font_dir() -> Path:
    """Diretoria de fontes do utilizador (freedesktop.org)."""
    return Path.home() / ".local" / "share" / "fonts"


@dataclass
class InstallResult:
    installed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_source(source: str | Path) -> tuple[bool, str]:
    """Valida um ficheiro candidato (extensão, tamanho, conteúdo)."""
    return test_font(source)


def refresh_font_cache(font_dir: Path) -> tuple[bool, str]:
    """Corre `fc-cache -f` para a diretoria. Retorna (ok, mensagem)."""
    try:
        subprocess.run(
            ["fc-cache", "-f", str(font_dir)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return False, "O comando fc-cache não está instalado (pacote fontconfig)."
    except subprocess.TimeoutExpired:
        return False, "O fc-cache excedeu o tempo limite (60s)."
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return False, f"fc-cache falhou: {detail}"
    except OSError as exc:
        return False, f"Falha ao executar fc-cache: {exc}"
    return True, "Cache de fontes atualizada."


def install_font_files(
    sources: list[str | Path],
    font_dir: Path | None = None,
    refresh_cache: bool = True,
) -> InstallResult:
    """Copia fontes validadas para ``font_dir``.

    - Rejeita symlinks, diretórios e formatos não suportados.
    - Valida o conteúdo com ``fc-scan`` antes de copiar.
    - Nunca sobrescreve: destinos existentes são reportados em ``skipped``.
    - Usa o nome base do ficheiro (sem componentes de diretoria),
      o que impede path traversal.
    """
    target = Path(font_dir) if font_dir is not None else get_default_font_dir()
    result = InstallResult()

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        for source in sources:
            result.errors.append(f"{Path(source).name}: não foi possível criar {target}: {exc}")
        return result

    for raw in sources:
        source = Path(raw)
        name = source.name  # sanitizado: sem diretórios

        ok, info = validate_source(source)
        if not ok:
            result.errors.append(f"{name}: {info}")
            continue

        destination = target / name
        try:
            if destination.exists() or destination.is_symlink():
                result.skipped.append(name)
                continue
            shutil.copy2(source, destination)
            result.installed.append(name)
        except OSError as exc:
            result.errors.append(f"{name}: {exc}")

    if result.installed and refresh_cache:
        cache_ok, cache_msg = refresh_font_cache(target)
        if not cache_ok:
            result.errors.append(cache_msg)

    return result

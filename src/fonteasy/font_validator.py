"""Validação de ficheiros de fontes via Fontconfig (fc-scan)."""

from __future__ import annotations

import subprocess
from pathlib import Path

SUPPORTED_EXTENSIONS = frozenset({".ttf", ".otf", ".ttc", ".otc"})

#: Limite de segurança por ficheiro (50 MiB). Evita cópias acidentais
#: de ficheiros gigantes e reduz o risco de DoS via ficheiros malformados.
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def test_font(file_path: str | Path) -> tuple[bool, str]:
    """Testa se o Fontconfig consegue analisar um ficheiro de fonte.

    Retorna ``(True, "Família — Estilo")`` se for válido, ou
    ``(False, "motivo")`` caso contrário. Nunca levanta exceções
    para entradas inválidas — apenas para erros de programação.
    """
    path = Path(file_path)

    if path.is_symlink():
        return False, "Ligações simbólicas não são aceites."

    if not path.is_file():
        return False, "O ficheiro não existe ou não é um ficheiro normal."

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, "Formato não suportado (usa .ttf, .otf, .ttc ou .otc)."

    try:
        size = path.stat().st_size
    except OSError:
        return False, "Não foi possível ler o ficheiro."

    if size == 0:
        return False, "O ficheiro está vazio."
    if size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"O ficheiro excede o limite de {max_mb} MiB."

    try:
        result = subprocess.run(
            ["fc-scan", "--format", "%{family[0]}|%{style[0]}", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError:
        return False, "O comando fc-scan não está instalado (pacote fontconfig)."
    except subprocess.TimeoutExpired:
        return False, "A análise excedeu o tempo limite."
    except OSError as exc:
        return False, f"Falha ao executar fc-scan: {exc}"

    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        return False, "O Fontconfig não conseguiu analisar esta fonte."

    # Formato esperado: "Família|Estilo". Fallback para o formato antigo
    # com quebras de linha, caso a versão do fontconfig seja diferente.
    if "|" in output:
        family, _, style = output.partition("|")
    else:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        family = lines[0] if lines else ""
        style = lines[1] if len(lines) > 1 else ""

    family = family.strip() or "Desconhecida"
    style = style.strip() or "Desconhecido"

    return True, f"{family} — {style}"

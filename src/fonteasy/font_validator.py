"""Validate font files via Fontconfig (fc-scan)."""

from __future__ import annotations

import subprocess
from pathlib import Path

SUPPORTED_EXTENSIONS = frozenset({".ttf", ".otf", ".ttc", ".otc"})

#: Per-file safety limit (50 MiB). Avoids accidental copies of huge
#: files and reduces the risk of DoS via malformed files.
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def test_font(file_path: str | Path) -> tuple[bool, str]:
    """Check whether Fontconfig can parse a font file.

    Returns ``(True, "Family — Style")`` when valid, or
    ``(False, "reason")`` otherwise. Never raises for invalid
    input — only for programming errors.
    """
    path = Path(file_path)

    if path.is_symlink():
        return False, "Symbolic links are not accepted."

    if not path.is_file():
        return False, "The file does not exist or is not a regular file."

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, "Unsupported format (use .ttf, .otf, .ttc or .otc)."

    try:
        size = path.stat().st_size
    except OSError:
        return False, "Could not read the file."

    if size == 0:
        return False, "The file is empty."
    if size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, "The file exceeds the {} MiB limit.".format(max_mb)

    try:
        result = subprocess.run(
            ["fc-scan", "--format", "%{family[0]}|%{style[0]}", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError:
        return False, "The fc-scan command is not installed (fontconfig package)."
    except subprocess.TimeoutExpired:
        return False, "Analysis timed out."
    except OSError as exc:
        return False, "Failed to run fc-scan: {}".format(exc)

    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        return False, "Fontconfig could not parse this font."

    # Expected format: "Family|Style". Fall back to the legacy
    # newline format for differing fontconfig versions.
    if "|" in output:
        family, _, style = output.partition("|")
    else:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        family = lines[0] if lines else ""
        style = lines[1] if len(lines) > 1 else ""

    family = family.strip() or "Unknown"
    style = style.strip() or "Unknown"

    return True, "{} — {}".format(family, style)

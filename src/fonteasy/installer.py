"""Font installation logic (no GTK dependency).

Kept separate from the UI so it can be tested with pytest and reused.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from fonteasy.font_validator import SUPPORTED_EXTENSIONS, test_font


def get_default_font_dir() -> Path:
    """User font directory (freedesktop.org)."""
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
    """Validate a candidate file (extension, size, contents)."""
    return test_font(source)


def refresh_font_cache(font_dir: Path) -> tuple[bool, str]:
    """Run `fc-cache -f` for the directory. Returns (ok, message)."""
    try:
        subprocess.run(
            ["fc-cache", "-f", str(font_dir)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return False, "The fc-cache command is not installed (fontconfig package)."
    except subprocess.TimeoutExpired:
        return False, "fc-cache timed out (60s)."
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return False, "fc-cache failed: {}".format(detail)
    except OSError as exc:
        return False, "Failed to run fc-cache: {}".format(exc)
    return True, "Font cache refreshed."


def install_font_files(
    sources: list[str | Path],
    font_dir: Path | None = None,
    refresh_cache: bool = True,
) -> InstallResult:
    """Copy validated fonts into ``font_dir``.

    - Rejects symlinks, directories and unsupported formats.
    - Validates contents with ``fc-scan`` before copying.
    - Never overwrites: existing destinations are reported in ``skipped``.
    - Uses only the file's base name (no directory components),
      which prevents path traversal.
    """
    target = Path(font_dir) if font_dir is not None else get_default_font_dir()
    result = InstallResult()

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        for source in sources:
            result.errors.append(
                "{}: could not create {}: {}".format(Path(source).name, target, exc)
            )
        return result

    for raw in sources:
        source = Path(raw)
        name = source.name  # sanitized: no directories

        ok, info = validate_source(source)
        if not ok:
            result.errors.append("{}: {}".format(name, info))
            continue

        destination = target / name
        try:
            if destination.exists() or destination.is_symlink():
                result.skipped.append(name)
                continue
            shutil.copy2(source, destination)
            result.installed.append(name)
        except OSError as exc:
            result.errors.append("{}: {}".format(name, exc))

    if result.installed and refresh_cache:
        cache_ok, cache_msg = refresh_font_cache(target)
        if not cache_ok:
            result.errors.append(cache_msg)

    return result

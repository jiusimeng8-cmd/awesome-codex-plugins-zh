#!/usr/bin/env python3
"""Apply maintained Chinese documentation overlays after each upstream sync.

Every file below translations/docs/ mirrors its target path below the repository
root. Only documentation extensions are allowed; source code and plugin
metadata stay owned by the upstream snapshot/localization generator.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAYS = ROOT / "translations" / "docs"
ALLOWED_SUFFIXES = {".md", ".mdx", ".rst", ".txt"}


def main() -> None:
    applied = 0
    for overlay in sorted(OVERLAYS.rglob("*")) if OVERLAYS.exists() else []:
        if not overlay.is_file():
            continue
        if overlay.name == ".gitkeep":
            continue
        target = ROOT / overlay.relative_to(OVERLAYS)
        if overlay.suffix.lower() not in ALLOWED_SUFFIXES:
            raise RuntimeError(f"Refusing non-document overlay: {overlay.relative_to(ROOT)}")
        if not target.is_relative_to(ROOT / "plugins"):
            raise RuntimeError(f"Overlay target must be under plugins/: {target.relative_to(ROOT)}")
        if not target.exists():
            raise RuntimeError(f"Upstream target no longer exists: {target.relative_to(ROOT)}")
        shutil.copyfile(overlay, target)
        applied += 1
    print(f"applied {applied} Chinese documentation overlays")


if __name__ == "__main__":
    main()

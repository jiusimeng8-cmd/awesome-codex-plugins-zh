#!/usr/bin/env python3
"""Validate Chinese documentation overlays without changing source files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAYS = ROOT / "translations" / "docs"
SOURCE_REF = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
FENCE = re.compile(r"(?ms)^(?:```|~~~)[^\n]*\n.*?^(?:```|~~~)\s*$")
# Stop at Markdown delimiters and Chinese punctuation.  Chinese prose often
# follows a URL without an ASCII space, so treating it as part of the URL
# creates false "missing URL" failures in otherwise valid translations.
URL = re.compile(r"https?://[^\s)>'\"`*，。；：！？、】【\u4e00-\u9fff]+")
URL_TRAILING_PUNCTUATION = ".,;:!?"


def urls(text: str) -> set[str]:
    """Return URLs while ignoring Markdown prose punctuation after a URL."""
    return {match.rstrip(URL_TRAILING_PUNCTUATION) for match in URL.findall(text)}


def source_text(relative: Path) -> str:
    process = subprocess.run(
        ["git", "show", f"{SOURCE_REF}:{relative.as_posix()}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.decode("utf-8", "replace").strip())
    return process.stdout.decode("utf-8", "replace")


def main() -> None:
    checked = 0
    failures: list[dict[str, object]] = []
    for overlay in sorted(OVERLAYS.rglob("*")) if OVERLAYS.exists() else []:
        if not overlay.is_file() or overlay.name == ".gitkeep":
            continue
        relative = overlay.relative_to(OVERLAYS)
        if not relative.as_posix().startswith("plugins/"):
            failures.append({"file": str(relative), "error": "target must be under plugins/"})
            continue
        try:
            source = source_text(relative)
        except RuntimeError as error:
            failures.append({"file": str(relative), "error": str(error)})
            continue
        translated = overlay.read_text(encoding="utf-8")
        source_fences = FENCE.findall(source)
        translated_fences = FENCE.findall(translated)
        if source_fences != translated_fences:
            failures.append(
                {
                    "file": str(relative),
                    "error": "fenced code blocks differ from source",
                    "source_blocks": len(source_fences),
                    "translated_blocks": len(translated_fences),
                }
            )
            continue
        missing_urls = sorted(urls(source) - urls(translated))
        if missing_urls:
            failures.append(
                {"file": str(relative), "error": "source URLs missing", "urls": missing_urls[:10]}
            )
            continue
        if not re.search(r"[\u4e00-\u9fff]", translated):
            failures.append({"file": str(relative), "error": "no Chinese text"})
            continue
        checked += 1
    result = {"source_ref": SOURCE_REF, "checked": checked, "failures": failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

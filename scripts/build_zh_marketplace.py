#!/usr/bin/env python3
"""Generate a Chinese Codex marketplace manifest from the upstream manifest.

Only presentation fields are localized. Plugin identifiers, local source paths,
icons, and installation/authentication policies remain byte-for-byte compatible
with the upstream marketplace.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CACHE = ROOT / "translations" / "zh-CN.json"
SOURCE = ROOT / "translations" / "source-marketplace.json"

CATEGORY_TRANSLATIONS = {
    "Development & Workflow": "开发与工作流",
    "Tools & Integrations": "工具与集成",
}
SERVICE_AVAILABLE = True


def save_cache(cache: dict[str, str]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def translate(text: str, cache: dict[str, str]) -> str:
    global SERVICE_AVAILABLE
    if not text or any("\u4e00" <= char <= "\u9fff" for char in text):
        return text
    if text in cache:
        return cache[text]
    if not SERVICE_AVAILABLE:
        return f"（英文原文）{text}"

    query = urllib.parse.urlencode({"q": text, "langpair": "en|zh-CN"})
    request = urllib.request.Request(
        f"https://api.mymemory.translated.net/get?{query}",
        headers={"User-Agent": "awesome-codex-plugins-zh-sync/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.load(response)
    except Exception as error:
        SERVICE_AVAILABLE = False
        print(f"translation unavailable; keeping English fallback: {error}", file=sys.stderr)
        return f"（英文原文）{text}"
    translated = payload.get("responseData", {}).get("translatedText", "").strip()
    if not translated:
        raise RuntimeError(f"Translation service returned no result for: {text}")
    cache[text] = translated
    # Make a partially completed first run resumable after CI timeouts or rate limits.
    save_cache(cache)
    time.sleep(0.25)
    return translated


def chinese_label(description: str) -> str:
    """Make a compact Chinese purpose label for the marketplace list view."""
    text = description.removeprefix("（英文原文）").strip()
    chinese_start = next(
        (index for index, char in enumerate(text) if "\u4e00" <= char <= "\u9fff"), None
    )
    if chinese_start is not None:
        text = text[chinese_start:]
    for separator in ("。", "；", "，", "：", "、", " "):
        text = text.split(separator, 1)[0]
    text = text.strip(" ，。；：、-—")
    if len(text) > 18:
        text = text[:18].rstrip(" ，。；：、-—") + "…"
    return text or "中文插件说明"


def main() -> None:
    if "--refresh-source" in sys.argv:
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE.write_bytes(MARKETPLACE.read_bytes())
    source = SOURCE if SOURCE.exists() else MARKETPLACE
    data = json.loads(source.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}

    data["name"] = "awesome-codex-plugins-zh"
    data.setdefault("interface", {})["displayName"] = "精选 Codex 插件（中文）"
    for plugin in data.get("plugins", []):
        plugin["category"] = CATEGORY_TRANSLATIONS.get(
            plugin.get("category", ""), plugin.get("category", "")
        )
        plugin["description"] = translate(plugin.get("description", ""), cache)
        # Keep the vendor/product brand searchable, while making its purpose
        # understandable to Chinese users without changing the plugin ID.
        brand = plugin.get("displayName") or plugin.get("name", "")
        plugin["displayName"] = f"{brand} · {chinese_label(plugin['description'])}"

    save_cache(cache)
    MARKETPLACE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

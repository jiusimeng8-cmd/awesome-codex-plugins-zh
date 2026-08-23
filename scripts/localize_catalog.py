#!/usr/bin/env python3
"""Build the Chinese, user-facing catalog from an upstream marketplace snapshot.

This script deliberately localizes only display metadata: the marketplace,
the registry index, and each plugin's public manifest.  It does not rename a
plugin ID, alter a source path, change code, or rewrite a Skill instruction.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGINS_INDEX = ROOT / "plugins.json"
SOURCE_MARKETPLACE = ROOT / "translations" / "source-marketplace.json"
SOURCE_PLUGINS_INDEX = ROOT / "translations" / "source-plugins.json"
CACHE = ROOT / "translations" / "zh-CN.json"

CATEGORY_TRANSLATIONS = {
    "Development & Workflow": "开发与工作流",
    "Tools & Integrations": "工具与集成",
    "Developer Tools": "开发者工具",
    "Productivity": "效率工具",
    "Coding": "编程开发",
}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contains_chinese(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def translated(value: str, cache: dict[str, str]) -> str:
    if not value or contains_chinese(value):
        return value
    result = cache.get(value)
    if not result or not contains_chinese(result):
        raise RuntimeError(
            "Missing Chinese translation for upstream text. "
            f"Add it to {CACHE.relative_to(ROOT)} before publishing: {value}"
        )
    return result


def purpose_label(description: str) -> str:
    text = description.strip()
    for separator in ("。", "；", "，", "：", "、"):
        text = text.split(separator, 1)[0]
    text = text.strip(" ，。；：、-—")
    if len(text) > 18:
        text = text[:18].rstrip(" ，。；：、-—") + "…"
    return text or "中文说明"


def localized_display_name(brand: str, description: str) -> str:
    base = brand.split(" · ", 1)[0].strip()
    return f"{base} · {purpose_label(description)}"


def local_category(category: str) -> str:
    return CATEGORY_TRANSLATIONS.get(category, category)


def plugin_path(value: str) -> str:
    return value.removeprefix("./").rstrip("/")


def build_marketplace(source: dict[str, object], cache: dict[str, str]) -> dict[str, object]:
    result = json.loads(json.dumps(source))
    result["name"] = "awesome-codex-plugins-zh"
    interface = result.setdefault("interface", {})
    if isinstance(interface, dict):
        interface["displayName"] = "精选 Codex 插件（中文）"
    for item in result.get("plugins", []):
        if not isinstance(item, dict):
            continue
        description = translated(str(item.get("description", "")), cache)
        item["description"] = description
        item["displayName"] = localized_display_name(
            str(item.get("displayName") or item.get("name") or "Codex 插件"), description
        )
        item["category"] = local_category(str(item.get("category", "")))
    return result


def build_index(source: dict[str, object], cache: dict[str, str]) -> dict[str, object]:
    result = json.loads(json.dumps(source))
    result["name"] = "awesome-codex-plugins-zh"
    result["categories"] = [local_category(str(value)) for value in result.get("categories", [])]
    for item in result.get("plugins", []):
        if not isinstance(item, dict):
            continue
        item["description"] = translated(str(item.get("description", "")), cache)
        item["category"] = local_category(str(item.get("category", "")))
        item["source"] = "awesome-codex-plugins-zh"
    return result


def source_entries(source: dict[str, object], cache: dict[str, str]) -> list[tuple[str, dict[str, str]]]:
    entries: list[tuple[str, dict[str, str]]] = []
    for item in source.get("plugins", []):
        if not isinstance(item, dict):
            continue
        source_info = item.get("source", {})
        if not isinstance(source_info, dict):
            continue
        raw_path = source_info.get("path")
        if not isinstance(raw_path, str):
            continue
        description = translated(str(item.get("description", "")), cache)
        entries.append(
            (
                plugin_path(raw_path),
                {
                    "description": description,
                    "brand": str(item.get("displayName") or item.get("name") or "Codex 插件"),
                    "category": local_category(str(item.get("category", ""))),
                },
            )
        )
    return sorted(entries, key=lambda pair: len(pair[0]), reverse=True)


def find_entry(path: Path, entries: list[tuple[str, dict[str, str]]]) -> dict[str, str] | None:
    relative = path.relative_to(ROOT).as_posix()
    for prefix, entry in entries:
        if relative == prefix or relative.startswith(prefix + "/"):
            return entry
    return None


def localize_manifest(path: Path, entry: dict[str, str]) -> bool:
    try:
        manifest = read_json(path)
    except json.JSONDecodeError:
        return False
    if not isinstance(manifest, dict):
        return False
    description = entry["description"]
    changed = manifest.get("description") != description
    manifest["description"] = description
    interface = manifest.get("interface")
    if isinstance(interface, dict):
        brand = str(interface.get("displayName") or entry["brand"])
        updates = {
            "displayName": localized_display_name(brand, description),
            "shortDescription": purpose_label(description),
            "longDescription": description,
            "category": entry["category"],
        }
        if isinstance(interface.get("capabilities"), list):
            updates["capabilities"] = [f"适用场景：{purpose_label(description)}"]
        if isinstance(interface.get("defaultPrompt"), list):
            updates["defaultPrompt"] = [
                f"使用 {brand.split(' · ', 1)[0]} 帮我：{purpose_label(description)}"
            ]
        for key, value in updates.items():
            if interface.get(key) != value:
                interface[key] = value
                changed = True
    if changed:
        write_json(path, manifest)
    return changed


def main() -> None:
    refresh = "--refresh-source" in sys.argv
    if refresh:
        SOURCE_MARKETPLACE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE_MARKETPLACE.write_bytes(MARKETPLACE.read_bytes())
        SOURCE_PLUGINS_INDEX.write_bytes(PLUGINS_INDEX.read_bytes())
    if not SOURCE_MARKETPLACE.exists() or not SOURCE_PLUGINS_INDEX.exists():
        raise RuntimeError("Missing upstream source snapshots; rerun with --refresh-source.")

    source_marketplace = read_json(SOURCE_MARKETPLACE)
    source_index = read_json(SOURCE_PLUGINS_INDEX)
    cache = read_json(CACHE)
    if not isinstance(source_marketplace, dict) or not isinstance(source_index, dict):
        raise RuntimeError("Source marketplace/index files must be JSON objects.")
    if not isinstance(cache, dict):
        raise RuntimeError("Translation cache must be a JSON object.")

    localized_marketplace = build_marketplace(source_marketplace, cache)
    localized_index = build_index(source_index, cache)
    write_json(MARKETPLACE, localized_marketplace)
    write_json(PLUGINS_INDEX, localized_index)

    entries = source_entries(source_marketplace, cache)
    manifests_seen = 0
    manifests_changed = 0
    for path in ROOT.glob("plugins/**/.codex-plugin/plugin.json"):
        entry = find_entry(path, entries)
        if entry is None:
            continue
        manifests_seen += 1
        manifests_changed += int(localize_manifest(path, entry))
    print(f"localized marketplace, index, and {manifests_changed}/{manifests_seen} manifests")


if __name__ == "__main__":
    main()

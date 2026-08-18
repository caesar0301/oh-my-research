#!/usr/bin/env python3
"""Lightweight collect CLI: record sources into materials/ + papers-index.json.

Full download handlers (arxiv SDK, git clone, etc.) can be layered later; this
CLI ensures workspace shape and index IDs for the report-first workflow.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def ensure_dirs(workspace: Path) -> None:
    for rel in (
        "materials/papers",
        "materials/web",
        "materials/github",
        "materials/datasets",
        "materials/search",
        "materials/failed",
        "docs/index",
    ):
        (workspace / rel).mkdir(parents=True, exist_ok=True)


def load_index(workspace: Path) -> dict[str, Any]:
    path = workspace / "docs" / "index" / "papers-index.json"
    if not path.exists():
        return {"papers": [], "web": [], "github": [], "search": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"papers": data, "web": [], "github": [], "search": []}
    for key in ("papers", "web", "github", "search"):
        data.setdefault(key, [])
    return data


def save_index(workspace: Path, data: dict[str, Any]) -> None:
    path = workspace / "docs" / "index" / "papers-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    md = workspace / "docs" / "index" / "papers-index.md"
    lines = ["# Materials Index", ""]
    for bucket in ("papers", "web", "github", "search"):
        lines.append(f"## {bucket}")
        for item in data.get(bucket, []):
            lines.append(
                f"- [{item['id']}] {item.get('title') or item.get('source')} — {item.get('source')}"
            )
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")


def next_id(items: list[dict[str, Any]], prefix: str) -> str:
    nums = []
    for it in items:
        m = re.match(rf"{prefix}-(\d+)", it.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    n = max(nums) + 1 if nums else 1
    return f"{prefix}-{n:03d}"


def classify(source: str) -> str:
    s = source.lower()
    if "arxiv.org" in s or re.match(r"^10\.\d+", s) or s.endswith(".pdf"):
        return "papers"
    if "github.com" in s:
        return "github"
    if "huggingface.co" in s:
        return "datasets"
    if s.startswith("http://") or s.startswith("https://"):
        return "web"
    return "search"


def record(workspace: Path, source: str, title: str | None = None) -> dict[str, Any]:
    ensure_dirs(workspace)
    data = load_index(workspace)
    kind = classify(source)
    now = datetime.now(timezone.utc).isoformat()

    if kind == "papers":
        item = {
            "id": next_id(data["papers"], "P"),
            "source": source,
            "title": title or source,
            "collected_at": now,
        }
        note = workspace / "materials" / "papers" / f"{item['id']}.source.txt"
        note.write_text(f"source: {source}\ntitle: {item['title']}\n", encoding="utf-8")
        item["path"] = str(note.relative_to(workspace))
        data["papers"].append(item)
    elif kind == "github":
        item = {
            "id": next_id(data["github"], "G"),
            "source": source,
            "title": title or urlparse(source).path.strip("/"),
            "collected_at": now,
        }
        note = workspace / "materials" / "github" / f"{item['id']}.source.txt"
        note.write_text(f"source: {source}\n", encoding="utf-8")
        item["path"] = str(note.relative_to(workspace))
        data["github"].append(item)
    elif kind == "web" or kind == "datasets":
        item = {
            "id": next_id(data["web"], "W"),
            "source": source,
            "title": title or source,
            "collected_at": now,
            "kind": kind,
        }
        note = workspace / "materials" / ("datasets" if kind == "datasets" else "web") / f"{item['id']}.source.txt"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"source: {source}\n", encoding="utf-8")
        item["path"] = str(note.relative_to(workspace))
        data["web"].append(item)
    else:
        item = {
            "id": next_id(data["search"], "S"),
            "source": source,
            "title": title or source,
            "collected_at": now,
            "kind": "search",
        }
        note = workspace / "materials" / "search" / f"{item['id']}.query.txt"
        note.write_text(f"query: {source}\n", encoding="utf-8")
        item["path"] = str(note.relative_to(workspace))
        data["search"].append(item)

    save_index(workspace, data)
    return item


def main() -> None:
    p = argparse.ArgumentParser(description="OMR collect CLI (index + placeholders)")
    p.add_argument("sources", nargs="+", help="URLs, DOIs, or search queries")
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.add_argument("--title", default=None)
    args = p.parse_args()
    ws = args.workspace.resolve()
    results = [record(ws, s, args.title) for s in args.sources]
    print(json.dumps({"recorded": results}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Lightweight collect CLI: record sources into materials/ + papers-index.json.

Creates only the directories needed for the files being written — never a full
empty materials/ tree. After recording a source, optionally invokes
`material_to_markdown.py` to download + convert the source into a full-text
Markdown file (`materials/<bucket>/<ID>.md`) so ANALYZE can read the entire
paper, not just the abstract.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_SCRIPT_DIR = Path(__file__).resolve().parent
_CONVERTER = _SCRIPT_DIR / "material_to_markdown.py"


def write_text(path: Path, text: str) -> None:
    """Create parent dirs only when writing a real file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
    write_text(path, json.dumps(data, indent=2) + "\n")
    md = workspace / "docs" / "index" / "papers-index.md"
    lines = ["# Materials Index", ""]
    for bucket in ("papers", "web", "github", "search"):
        items = data.get(bucket, [])
        if not items:
            continue  # skip empty sections — and never invent empty bucket dirs
        lines.append(f"## {bucket}")
        for item in items:
            lines.append(
                f"- [{item['id']}] {item.get('title') or item.get('source')} — {item.get('source')}"
            )
        lines.append("")
    write_text(md, "\n".join(lines).rstrip() + "\n")


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
    if s.startswith(("http://", "https://")):
        return "web"
    return "search"


def convert_source(
    workspace: Path, source: str, material_id: str, bucket: str, title: str | None
) -> dict[str, Any]:
    """Invoke material_to_markdown.py to download + convert one source.

    Returns the converter's result dict (status / method / path / ...). On
    any invocation error, returns a failed record with the reason."""
    if not _CONVERTER.exists():
        return {
            "id": material_id,
            "status": "failed",
            "reason": "converter script not found",
        }
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(_CONVERTER),
                source,
                "--id",
                material_id,
                "--bucket",
                bucket,
                "--workspace",
                str(workspace),
                "--title",
                title or "",
            ],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return {
            "id": material_id,
            "status": "failed",
            "reason": result.stderr.strip() or f"converter exit {result.returncode}",
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {
            "id": material_id,
            "status": "failed",
            "reason": f"{type(e).__name__}: {e}",
        }


def record(
    workspace: Path,
    source: str,
    title: str | None = None,
    convert: bool = True,
) -> dict[str, Any]:
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
        write_text(note, f"source: {source}\ntitle: {item['title']}\n")
        item["path"] = str(note.relative_to(workspace))
        if convert:
            conv = convert_source(
                workspace, source, item["id"], "papers", item["title"]
            )
            item["markdown_path"] = conv.get("path", "")
            item["markdown_status"] = conv.get("status", "")
            item["markdown_method"] = conv.get("method", "")
            if conv.get("reason"):
                item["markdown_failure_reason"] = conv["reason"]
        data["papers"].append(item)
    elif kind == "github":
        item = {
            "id": next_id(data["github"], "G"),
            "source": source,
            "title": title or urlparse(source).path.strip("/"),
            "collected_at": now,
        }
        note = workspace / "materials" / "github" / f"{item['id']}.source.txt"
        write_text(note, f"source: {source}\n")
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
        dest = "datasets" if kind == "datasets" else "web"
        note = workspace / "materials" / dest / f"{item['id']}.source.txt"
        write_text(note, f"source: {source}\n")
        item["path"] = str(note.relative_to(workspace))
        if convert:
            conv = convert_source(workspace, source, item["id"], dest, item["title"])
            item["markdown_path"] = conv.get("path", "")
            item["markdown_status"] = conv.get("status", "")
            item["markdown_method"] = conv.get("method", "")
            if conv.get("reason"):
                item["markdown_failure_reason"] = conv["reason"]
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
        write_text(note, f"query: {source}\n")
        item["path"] = str(note.relative_to(workspace))
        data["search"].append(item)

    save_index(workspace, data)
    return item


def main() -> None:
    p = argparse.ArgumentParser(description="OMR collect CLI (index + placeholders)")
    p.add_argument("sources", nargs="+", help="URLs, DOIs, or search queries")
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.add_argument("--title", default=None)
    p.add_argument(
        "--convert",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="download + convert each source to full-text Markdown via anydoc (default: on)",
    )
    args = p.parse_args()
    ws = args.workspace.resolve()
    results = [record(ws, s, args.title, convert=args.convert) for s in args.sources]
    print(json.dumps({"recorded": results}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Initialize a minimal OMR workspace (AGENTS.md + .omr state)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(topic: str) -> str:
    s = topic.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "research-project"


def main() -> None:
    p = argparse.ArgumentParser(description="OMR init workspace")
    p.add_argument("topic")
    p.add_argument("--workspace", type=Path, default=None, help="Defaults to ./<slug>")
    p.add_argument("--in-place", action="store_true", help="Use current directory")
    args = p.parse_args()

    slug = slugify(args.topic)
    if args.in_place:
        root = Path.cwd()
    elif args.workspace:
        root = args.workspace
    else:
        root = Path.cwd() / slug
    root.mkdir(parents=True, exist_ok=True)
    omr = root / ".omr"
    omr.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    template = (
        Path(__file__).resolve().parents[1] / "assets" / "templates" / "AGENTS.md.template"
    ).read_text(encoding="utf-8")
    agents = (
        template.replace("{{PROJECT_NAME}}", slug)
        .replace("{{RESEARCH_QUESTION}}", args.topic)
        .replace("{{STATUS}}", "initialized")
        .replace("{{ACTIVE_PATTERN}}", "Evidence-Deep")
        .replace("{{CREATED_AT}}", now)
        .replace("{{LAST_UPDATED}}", now)
    )
    (root / "AGENTS.md").write_text(agents, encoding="utf-8")

    state = {
        "unlocked": ["init", "collect", "idea", "think"],
        "ready": [],
        "locked": ["analyze", "synth", "decide", "reconcile"],
        "completed": ["init"],
    }
    (omr / "tree-state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    pattern = {
        "name": "Evidence-Deep",
        "source": "skills/oh-my-research/patterns/evidence-deep.json",
    }
    (omr / "pattern.json").write_text(json.dumps(pattern, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"workspace": str(root), "pattern": "Evidence-Deep"}, indent=2))


if __name__ == "__main__":
    main()

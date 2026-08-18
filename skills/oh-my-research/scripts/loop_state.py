#!/usr/bin/env python3
"""Loop-state helper for OMR Loop pattern (Gate L)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT = {
    "active": False,
    "mode": None,
    "iteration": 0,
    "focus_question": "",
    "gaps": [],
    "history": [],
}


def path(workspace: Path) -> Path:
    return workspace / ".omr" / "loop-state.json"


def load(workspace: Path) -> dict[str, Any]:
    p = path(workspace)
    if not p.exists():
        return json.loads(json.dumps(DEFAULT))
    return json.loads(p.read_text(encoding="utf-8"))


def save(workspace: Path, state: dict[str, Any]) -> None:
    p = path(workspace)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def activate(workspace: Path, mode: str, focus: str) -> dict[str, Any]:
    state = load(workspace)
    state.update(
        {
            "active": True,
            "mode": mode,
            "iteration": 1,
            "focus_question": focus,
            "gaps": state.get("gaps") or [],
            "history": state.get("history") or [],
        }
    )
    state["history"].append(
        {"at": datetime.now(timezone.utc).isoformat(), "event": "activate", "mode": mode}
    )
    save(workspace, state)
    return state


def iterate(workspace: Path, note: str = "") -> dict[str, Any]:
    state = load(workspace)
    state["iteration"] = int(state.get("iteration") or 0) + 1
    state["history"].append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "event": "iterate",
            "note": note,
            "iteration": state["iteration"],
        }
    )
    save(workspace, state)
    return state


def advance(workspace: Path) -> dict[str, Any]:
    state = load(workspace)
    state["active"] = False
    state["history"].append(
        {"at": datetime.now(timezone.utc).isoformat(), "event": "advance"}
    )
    save(workspace, state)
    return state


def main() -> None:
    p = argparse.ArgumentParser(description="OMR loop-state helper")
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    a = sub.add_parser("activate")
    a.add_argument("--mode", choices=["idea-dev", "deep-analyze"], required=True)
    a.add_argument("--focus", default="")
    i = sub.add_parser("iterate")
    i.add_argument("--note", default="")
    sub.add_parser("advance")
    args = p.parse_args()
    ws = args.workspace.resolve()
    if args.cmd == "show":
        print(json.dumps(load(ws), indent=2))
    elif args.cmd == "activate":
        print(json.dumps(activate(ws, args.mode, args.focus), indent=2))
    elif args.cmd == "iterate":
        print(json.dumps(iterate(ws, args.note), indent=2))
    elif args.cmd == "advance":
        print(json.dumps(advance(ws), indent=2))


if __name__ == "__main__":
    main()

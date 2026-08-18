#!/usr/bin/env python3
"""Tree-state helpers for Oh-My-Research workspaces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_STATE = {
    "unlocked": ["init", "collect", "idea", "think"],
    "ready": [],
    "locked": ["analyze", "synth", "decide", "reconcile"],
    "completed": [],
}


def omr_dir(workspace: Path) -> Path:
    return workspace / ".omr"


def state_path(workspace: Path) -> Path:
    return omr_dir(workspace) / "tree-state.json"


def load_state(workspace: Path) -> dict[str, Any]:
    path = state_path(workspace)
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_STATE))
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(workspace: Path, state: dict[str, Any]) -> None:
    d = omr_dir(workspace)
    d.mkdir(parents=True, exist_ok=True)
    state_path(workspace).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _move(state: dict[str, Any], op: str, bucket: str) -> None:
    for key in ("unlocked", "ready", "locked", "completed"):
        if op in state.get(key, []):
            state[key] = [x for x in state[key] if x != op]
    state.setdefault(bucket, []).append(op)


def complete(workspace: Path, op: str) -> dict[str, Any]:
    state = load_state(workspace)
    _move(state, op, "completed")
    if op == "init":
        for x in ("collect", "idea", "think"):
            if x not in state["completed"] and x not in state["unlocked"]:
                state.setdefault("unlocked", []).append(x)
    if op == "collect":
        if "analyze" in state.get("locked", []):
            state["locked"] = [x for x in state["locked"] if x != "analyze"]
        if "analyze" not in state.get("ready", []) and "analyze" not in state.get("completed", []):
            state.setdefault("ready", []).append("analyze")
    if op == "analyze":
        # Gate A pass should call unlock_synth separately; still mark analyze done
        pass
    if op == "synth":
        pass
    save_state(workspace, state)
    return state


def unlock_synth(workspace: Path) -> dict[str, Any]:
    state = load_state(workspace)
    if "synth" in state.get("locked", []):
        state["locked"] = [x for x in state["locked"] if x != "synth"]
    if "synth" not in state.get("ready", []) and "synth" not in state.get("completed", []):
        state.setdefault("ready", []).append("synth")
    if "decide" in state.get("locked", []):
        state["locked"] = [x for x in state["locked"] if x != "decide"]
        if "decide" not in state.get("unlocked", []):
            state.setdefault("unlocked", []).append("decide")
    if "reconcile" in state.get("locked", []):
        state["locked"] = [x for x in state["locked"] if x != "reconcile"]
        if "reconcile" not in state.get("unlocked", []):
            state.setdefault("unlocked", []).append("reconcile")
    save_state(workspace, state)
    return state


def show(workspace: Path) -> None:
    state = load_state(workspace)
    print(json.dumps(state, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="OMR tree-state helper")
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show")
    init_p = sub.add_parser("init")
    init_p.add_argument("--reset", action="store_true")

    c = sub.add_parser("complete")
    c.add_argument("op")

    sub.add_parser("unlock-synth")

    args = p.parse_args()
    ws = args.workspace.resolve()
    if args.cmd == "show":
        show(ws)
    elif args.cmd == "init":
        if args.reset or not state_path(ws).exists():
            st = json.loads(json.dumps(DEFAULT_STATE))
            st["completed"] = ["init"]
            save_state(ws, st)
        show(ws)
    elif args.cmd == "complete":
        complete(ws, args.op)
        show(ws)
    elif args.cmd == "unlock-synth":
        unlock_synth(ws)
        show(ws)


if __name__ == "__main__":
    main()

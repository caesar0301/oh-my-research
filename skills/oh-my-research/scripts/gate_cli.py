#!/usr/bin/env python3
"""Mechanical gate-mode and confirmation enforcement for Oh-My-Research.

This script never judges research quality. It only enforces:

* the persisted gate mode (semi-automated by default),
* the confirmation fields on gate JSON files,
* gate-chain completeness before ANALYZE / SYNTH / export.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workspace_root import resolve_workspace_root

MODES = ("semi-automated", "quick-pass", "fully-automated")

EXPLICIT_PHRASES = (
    "quick-pass",
    "quick pass",
    "no confirmations",
    "no confirmation",
    "skip confirmations",
    "skip confirmation",
    "fully automated",
    "fully-automated",
    "不要确认",
    "无需确认",
    "不用确认",
    "不用问",
    "跳过确认",
    "不要暂停",
    "直接跑完",
    "自动继续",
)

GATE_FILES = {
    "M": "gate-m.json",
    "T": "gate-t.json",
    "A": "gate-a.json",
    "QA1": "QA1-evidence-analysis.json",
    "P": "gate-p.json",
    "Lenses": "lenses.json",
    "D": "gate-d.json",
    "QA2": "QA2-pre-export.json",
}

GATE_REQUIRES = {
    "M": (),
    "T": ("M",),
    "A": ("M", "T"),
    "QA1": ("M", "T", "A"),
    "P": ("M", "T", "A"),
    "Lenses": ("P",),
    "D": ("P", "Lenses"),
    "QA2": ("D",),
}

STAGE_GATES = {
    "analyze": ("M",),
    "synth": ("M", "T", "A", "QA1", "P"),
    "publish": ("M", "T", "A", "QA1", "P", "Lenses", "D", "QA2"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_workspace(workspace: str | None) -> Path:
    return resolve_workspace_root(workspace)


def mode_path(workspace: Path) -> Path:
    return workspace / ".omr" / "gate-mode.json"


def gates_dir(workspace: Path) -> Path:
    return workspace / ".omr" / "quality-gates"


def default_mode() -> dict[str, Any]:
    return {
        "mode": "semi-automated",
        "source": "default",
        "set_at": None,
        "user_request": None,
        "pattern": None,
    }


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_mode(workspace: Path) -> tuple[dict[str, Any], bool]:
    path = mode_path(workspace)
    if not path.is_file():
        return default_mode(), False
    data = read_json(path)
    if data.get("mode") not in MODES:
        raise ValueError(f"invalid gate mode in {path}: {data.get('mode')!r}")
    return data, True


def write_mode(workspace: Path, data: dict[str, Any]) -> None:
    path = mode_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def has_explicit_user_request(phrase: str | None) -> bool:
    if not phrase:
        return False
    lowered = phrase.strip().lower()
    return any(token in lowered for token in EXPLICIT_PHRASES)


def gate_path(workspace: Path, gate: str) -> Path:
    return gates_dir(workspace) / GATE_FILES[gate]


def load_gate(path: Path) -> dict[str, Any]:
    return read_json(path)


def emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def parse_checks(raw: str | None) -> list[Any]:
    if not raw:
        return []
    if raw.startswith("@"):
        data = json.loads(Path(raw[1:]).read_text(encoding="utf-8"))
    else:
        data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("--checks must be a JSON array")
    return data


def validate_gate_shape(
    gate: str,
    data: dict[str, Any],
    mode: dict[str, Any],
    path: Path,
) -> list[str]:
    issues: list[str] = []
    prefix = f"{path.name}: "
    if data.get("status") != "pass":
        issues.append(prefix + "status must be 'pass'")
    for field in ("decision_source", "pause", "confirmed_at", "user_decision"):
        if field not in data:
            issues.append(prefix + f"missing required field '{field}'")

    active_mode = mode.get("mode")
    source = data.get("decision_source")
    pause = data.get("pause")
    user_decision = data.get("user_decision")
    confirmed_at = data.get("confirmed_at")

    if active_mode == "semi-automated":
        if source != "user":
            issues.append(
                prefix + "semi-automated mode requires decision_source='user'"
            )
        if pause is not True:
            issues.append(prefix + "semi-automated mode requires pause=true")
        if not user_decision:
            issues.append(
                prefix + "semi-automated mode requires a non-empty user_decision"
            )
        if not confirmed_at:
            issues.append(prefix + "semi-automated mode requires confirmed_at")
    elif active_mode in ("quick-pass", "fully-automated"):
        if source not in ("agent", "legacy"):
            issues.append(
                prefix
                + f"{active_mode} mode requires decision_source='agent' or 'legacy'"
            )
        if pause is not False:
            issues.append(prefix + f"{active_mode} mode requires pause=false")
        if active_mode == "quick-pass":
            note = str(data.get("scenario_note") or "")
            if "quick-pass" not in note.lower():
                issues.append(
                    prefix
                    + "quick-pass mode requires a scenario_note mentioning quick-pass"
                )

    return issues


def validate_chain(workspace: Path, stage: str, mode: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if mode.get("mode") == "fully-automated":
        return issues

    required = STAGE_GATES[stage]
    for gate in required:
        path = gate_path(workspace, gate)
        if not path.is_file():
            issues.append(f"missing gate file {path.name} for stage '{stage}'")
            continue
        try:
            data = load_gate(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{path.name}: unreadable JSON ({exc})")
            continue
        issues.extend(validate_gate_shape(gate, data, mode, path))

        for prerequisite in GATE_REQUIRES[gate]:
            prereq_path = gate_path(workspace, prerequisite)
            if not prereq_path.is_file():
                issues.append(
                    f"{path.name}: prerequisite {prereq_path.name} is missing"
                )
                continue
            try:
                prereq_data = load_gate(prereq_path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                issues.append(f"{prereq_path.name}: unreadable JSON ({exc})")
                continue
            if prereq_data.get("status") != "pass":
                issues.append(
                    f"{path.name}: prerequisite {prereq_path.name} is not pass"
                )

    for path in sorted(gates_dir(workspace).glob("*.json")):
        if path.name not in GATE_FILES.values():
            issues.append(f"{path.name}: unknown gate file")
            continue
        if path.stem in ("QA1-evidence-analysis", "QA2-pre-export"):
            gate = "QA1" if path.stem.startswith("QA1") else "QA2"
        elif path.stem == "lenses":
            gate = "Lenses"
        elif path.stem.startswith("gate-"):
            gate = path.stem.removeprefix("gate-").upper()
        else:
            issues.append(f"{path.name}: unrecognized gate file")
            continue
        if gate not in required:
            try:
                data = load_gate(path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                issues.append(f"{path.name}: unreadable JSON ({exc})")
                continue
            issues.extend(validate_gate_shape(gate, data, mode, path))

    if mode.get("mode") == "quick-pass":
        if mode.get("source") != "user":
            issues.append("gate-mode.json: quick-pass requires source='user'")
        if not has_explicit_user_request(str(mode.get("user_request") or "")):
            issues.append(
                "gate-mode.json: quick-pass requires a stored explicit user request"
            )

    return issues


def cmd_init(args: argparse.Namespace) -> int:
    workspace = default_workspace(args.workspace)
    path = mode_path(workspace)
    if path.is_file() and not args.force:
        return emit(
            {
                "ok": True,
                "workspace": str(workspace),
                "action": "unchanged",
                "mode": load_mode(workspace)[0],
            }
        )
    data = default_mode()
    data["set_at"] = utc_now()
    write_mode(workspace, data)
    return emit(
        {"ok": True, "workspace": str(workspace), "action": "written", "mode": data}
    )


def cmd_show(args: argparse.Namespace) -> int:
    workspace = default_workspace(args.workspace)
    data, persisted = load_mode(workspace)
    return emit(
        {"ok": True, "workspace": str(workspace), "persisted": persisted, "mode": data}
    )


def cmd_set(args: argparse.Namespace) -> int:
    workspace = default_workspace(args.workspace)
    if args.pattern:
        if args.pattern != "rapid" or args.mode != "fully-automated":
            return emit(
                {
                    "ok": False,
                    "error": "--pattern rapid requires --mode fully-automated",
                },
                2,
            )
        if args.user_request:
            return emit(
                {
                    "ok": False,
                    "error": "use either --pattern rapid or --user-request, not both",
                },
                2,
            )
        data = {
            "mode": "fully-automated",
            "source": "pattern",
            "set_at": utc_now(),
            "user_request": None,
            "pattern": "rapid",
        }
    else:
        if not has_explicit_user_request(args.user_request):
            return emit(
                {
                    "ok": False,
                    "error": "changing gate mode requires an explicit user request (quick-pass / no confirmations / 不要确认 / …)",
                },
                2,
            )
        data = {
            "mode": args.mode,
            "source": "user",
            "set_at": utc_now(),
            "user_request": args.user_request.strip(),
            "pattern": None,
        }
    write_mode(workspace, data)
    return emit(
        {"ok": True, "workspace": str(workspace), "action": "written", "mode": data}
    )


def cmd_record(args: argparse.Namespace) -> int:
    workspace = default_workspace(args.workspace)
    mode, persisted = load_mode(workspace)
    if not persisted:
        return emit({"ok": False, "error": "run gate_cli.py init first"}, 2)

    gate = args.gate.upper() if args.gate.upper() in GATE_FILES else args.gate
    if gate not in GATE_FILES:
        return emit({"ok": False, "error": f"unknown gate {args.gate!r}"}, 2)

    path = gate_path(workspace, gate)
    if path.is_file() and not args.force:
        return emit(
            {
                "ok": False,
                "error": f"{path.name} already exists; use --force to overwrite",
            },
            2,
        )

    if mode.get("mode") != "fully-automated":
        for prerequisite in GATE_REQUIRES[gate]:
            prereq_path = gate_path(workspace, prerequisite)
            if not prereq_path.is_file():
                return emit(
                    {
                        "ok": False,
                        "error": f"prerequisite {prereq_path.name} is missing for {path.name}",
                    },
                    2,
                )
            if load_gate(prereq_path).get("status") != "pass":
                return emit(
                    {
                        "ok": False,
                        "error": f"prerequisite {prereq_path.name} is not pass",
                    },
                    2,
                )

    try:
        checks = parse_checks(args.checks)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit({"ok": False, "error": f"invalid --checks: {exc}"}, 2)

    active_mode = mode.get("mode")
    if active_mode == "semi-automated":
        if args.decision_source != "user":
            return emit(
                {
                    "ok": False,
                    "error": "semi-automated mode requires --decision-source user",
                },
                2,
            )
        if not args.user_decision:
            return emit(
                {"ok": False, "error": "semi-automated mode requires --user-decision"},
                2,
            )
        decision_source = "user"
        pause = True
        user_decision = args.user_decision.strip()
        confirmed_at = args.confirmed_at or utc_now()
    elif active_mode in ("quick-pass", "fully-automated"):
        decision_source = "agent"
        pause = False
        user_decision = None
        confirmed_at = None
    else:  # pragma: no cover - load_mode validates MODES
        return emit({"ok": False, "error": f"unsupported mode {active_mode!r}"}, 2)

    scenario_note = args.scenario_note or ""
    if active_mode == "quick-pass" and "quick-pass" not in scenario_note.lower():
        request = mode.get("user_request") or "explicit user request"
        scenario_note = f"quick-pass (user request: {request})" + (
            f"; {scenario_note}" if scenario_note else ""
        )

    payload = {
        "gate": gate,
        "run_at": utc_now(),
        "status": args.status,
        "scenario_note": scenario_note,
        "decision_source": decision_source,
        "pause": pause,
        "user_decision": user_decision,
        "confirmed_at": confirmed_at,
        "checks": checks,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return emit(
        {
            "ok": True,
            "workspace": str(workspace),
            "gate": gate,
            "file": str(path),
            "mode": active_mode,
        }
    )


def cmd_validate(args: argparse.Namespace) -> int:
    workspace = default_workspace(args.workspace)
    mode, persisted = load_mode(workspace)
    issues: list[str] = []
    if not persisted:
        issues.append("gate-mode.json is missing; run gate_cli.py init during INIT")
    stage = "publish" if args.stage == "all" else args.stage
    issues.extend(validate_chain(workspace, stage, mode))
    report = {
        "ok": not issues,
        "workspace": str(workspace),
        "mode": mode,
        "stage": stage,
        "gates_checked": [GATE_FILES[g] for g in STAGE_GATES[stage]],
        "issues": issues,
    }
    return emit(report, 0 if not issues else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_workspace(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--workspace",
            help="active OMR workspace (default: <cwd>/.omr)",
        )

    init_parser = subparsers.add_parser(
        "init", help="persist the default semi-automated gate mode"
    )
    add_workspace(init_parser)
    init_parser.add_argument(
        "--force", action="store_true", help="overwrite an existing gate-mode.json"
    )
    init_parser.set_defaults(func=cmd_init)

    show_parser = subparsers.add_parser("show", help="print the current gate mode")
    add_workspace(show_parser)
    show_parser.set_defaults(func=cmd_show)

    set_parser = subparsers.add_parser(
        "set", help="change gate mode from an explicit user request"
    )
    add_workspace(set_parser)
    set_parser.add_argument("--mode", choices=MODES, required=True)
    set_parser.add_argument(
        "--user-request", help="verbatim user phrase authorizing the change"
    )
    set_parser.add_argument(
        "--pattern",
        choices=("rapid",),
        help="Rapid pattern selects fully-automated gates",
    )
    set_parser.set_defaults(func=cmd_set)

    record_parser = subparsers.add_parser(
        "record", help="write one gate JSON with confirmation fields"
    )
    add_workspace(record_parser)
    record_parser.add_argument("--gate", required=True, choices=tuple(GATE_FILES))
    record_parser.add_argument(
        "--status", choices=("pass", "warn", "fail"), default="pass"
    )
    record_parser.add_argument("--scenario-note", default="")
    record_parser.add_argument(
        "--checks", help="JSON array or @file containing the checks list"
    )
    record_parser.add_argument(
        "--decision-source", choices=("user", "agent"), default="agent"
    )
    record_parser.add_argument(
        "--user-decision",
        help="verbatim user decision (required in semi-automated mode)",
    )
    record_parser.add_argument(
        "--confirmed-at", help="ISO-8601 timestamp of the user decision"
    )
    record_parser.add_argument(
        "--force", action="store_true", help="overwrite an existing gate JSON"
    )
    record_parser.set_defaults(func=cmd_record)

    validate_parser = subparsers.add_parser(
        "validate", help="validate gate mode, chain, and confirmations"
    )
    add_workspace(validate_parser)
    validate_parser.add_argument(
        "--stage", choices=(*STAGE_GATES, "all"), required=True
    )
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit({"ok": False, "error": str(exc)}, 2)


if __name__ == "__main__":
    sys.exit(main())

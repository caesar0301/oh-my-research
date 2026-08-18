#!/usr/bin/env python3
"""Skill-package version management for oh-my-research.

Single source of truth: skills/oh-my-research/VERSION

Synced locations:
  - skills/oh-my-research/SKILL.md          (metadata.version)
  - .claude-plugin/marketplace.json        (metadata.version + plugins[0].version)

Workspace research tags/backups are handled by version_control.py — not this script.

Commands:
  show                         Print current VERSION
  check                        Exit 0 if all locations match VERSION
  sync                         Write VERSION into SKILL.md + marketplace.json
  set <X.Y.Z> [--date YYYY-MM-DD] [--message TEXT]
                               Set VERSION, sync, prepend CHANGELOG stub
  bump major|minor|patch [--date YYYY-MM-DD] [--message TEXT]
                               Semver bump, sync, prepend CHANGELOG stub
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")
SKILL_VERSION_RE = re.compile(
    r'(^metadata:\s*\n(?:^[ \t]+.*\n)*?[ \t]+version:\s*)(["\']?)([^"\'\n]+)(["\']?)',
    re.M,
)


def repo_root() -> Path:
    # scripts/skill_version.py → skills/oh-my-research/scripts → … → repo root
    here = Path(__file__).resolve()
    # Prefer walking up until marketplace.json is found
    for parent in [here.parent, *here.parents]:
        if (parent / ".claude-plugin" / "marketplace.json").exists():
            return parent
        if (parent / "skills" / "oh-my-research" / "SKILL.md").exists() and (
            parent / ".claude-plugin"
        ).exists():
            return parent
    # Fallback: skills/oh-my-research/scripts → ../../../
    return here.parents[3]


def paths(root: Path) -> dict[str, Path]:
    return {
        "version": root / "skills" / "oh-my-research" / "VERSION",
        "skill": root / "skills" / "oh-my-research" / "SKILL.md",
        "marketplace": root / ".claude-plugin" / "marketplace.json",
        "changelog": root / "CHANGELOG.md",
    }


def read_version_file(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing VERSION file: {path}")
    value = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    if not SEMVER.match(value):
        raise SystemExit(f"Invalid semver in {path}: {value!r}")
    return value


def parse_semver(value: str) -> tuple[int, int, int]:
    match = SEMVER.match(value)
    if not match:
        raise SystemExit(f"Invalid semver: {value!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_semver(value: str, kind: str) -> str:
    major, minor, patch = parse_semver(value)
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"Unknown bump kind: {kind}")


def skill_md_version(text: str) -> str | None:
    match = SKILL_VERSION_RE.search(text)
    return match.group(3).strip() if match else None


def set_skill_md_version(text: str, version: str) -> str:
    if not SKILL_VERSION_RE.search(text):
        raise SystemExit("Could not find metadata.version in SKILL.md")
    return SKILL_VERSION_RE.sub(
        lambda m: f'{m.group(1)}"{version}"',
        text,
        count=1,
    )


def marketplace_versions(data: dict) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    meta = data.get("metadata") or {}
    if "version" in meta:
        found.append(("metadata.version", str(meta["version"])))
    for i, plugin in enumerate(data.get("plugins") or []):
        if "version" in plugin:
            found.append((f"plugins[{i}].version", str(plugin["version"])))
    return found


def set_marketplace_versions(data: dict, version: str) -> None:
    data.setdefault("metadata", {})["version"] = version
    for plugin in data.get("plugins") or []:
        plugin["version"] = version


def collect_versions(p: dict[str, Path]) -> dict[str, str]:
    versions: dict[str, str] = {"VERSION": read_version_file(p["version"])}
    skill_text = p["skill"].read_text(encoding="utf-8")
    skill_ver = skill_md_version(skill_text)
    if skill_ver is None:
        raise SystemExit("metadata.version missing in SKILL.md")
    versions["SKILL.md"] = skill_ver
    market = json.loads(p["marketplace"].read_text(encoding="utf-8"))
    for label, value in marketplace_versions(market):
        versions[f"marketplace.json:{label}"] = value
    return versions


def cmd_show(p: dict[str, Path]) -> int:
    print(read_version_file(p["version"]))
    return 0


def cmd_check(p: dict[str, Path]) -> int:
    versions = collect_versions(p)
    expected = versions["VERSION"]
    mismatches = {k: v for k, v in versions.items() if v != expected}
    if mismatches:
        print(f"VERSION={expected}")
        for key, value in mismatches.items():
            print(f"  MISMATCH {key}={value}")
        return 1
    print(f"OK — all locations at {expected}")
    for key, value in versions.items():
        print(f"  {key}: {value}")
    return 0


def write_version_file(path: Path, version: str) -> None:
    path.write_text(version + "\n", encoding="utf-8")


def sync_to_files(p: dict[str, Path], version: str) -> None:
    write_version_file(p["version"], version)
    skill_text = p["skill"].read_text(encoding="utf-8")
    p["skill"].write_text(set_skill_md_version(skill_text, version), encoding="utf-8")
    market = json.loads(p["marketplace"].read_text(encoding="utf-8"))
    set_marketplace_versions(market, version)
    p["marketplace"].write_text(
        json.dumps(market, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def prepend_changelog(path: Path, version: str, when: str, message: str | None) -> None:
    heading = f"## [{version}] — {when}\n"
    body = (
        f"\n### Changed\n\n- {message.strip()}\n"
        if message and message.strip()
        else "\n### Added\n\n- \n\n### Changed\n\n- \n\n### Fixed\n\n- \n"
    )
    entry = heading + body + "\n"
    if not path.exists():
        path.write_text(
            "# Changelog\n\n"
            "All notable changes to the **oh-my-research** skill package are documented here.\n\n"
            + entry,
            encoding="utf-8",
        )
        return
    text = path.read_text(encoding="utf-8")
    # Insert after the preamble (before the first ## [version] heading)
    match = re.search(r"^## \[", text, re.M)
    if match:
        text = text[: match.start()] + entry + text[match.start() :]
    else:
        text = text.rstrip() + "\n\n" + entry
    # Avoid duplicate heading for same version
    if text.count(f"## [{version}]") > 1:
        # Keep only the newly prepended one: drop older duplicates below
        parts = re.split(rf"(?=^## \[{re.escape(version)}\])", text, flags=re.M)
        kept = [parts[0]]
        version_blocks = [b for b in parts[1:] if b.startswith(f"## [{version}]")]
        other = [b for b in parts[1:] if not b.startswith(f"## [{version}]")]
        if version_blocks:
            kept.append(version_blocks[0])
        kept.extend(other)
        text = "".join(kept)
    path.write_text(text, encoding="utf-8")


def cmd_sync(p: dict[str, Path]) -> int:
    version = read_version_file(p["version"])
    sync_to_files(p, version)
    print(f"Synced {version} → SKILL.md + marketplace.json")
    return cmd_check(p)


def cmd_set(p: dict[str, Path], version: str, when: str, message: str | None) -> int:
    parse_semver(version)  # validate
    sync_to_files(p, version)
    prepend_changelog(p["changelog"], version, when, message)
    print(f"Set version {version}")
    return cmd_check(p)


def cmd_bump(p: dict[str, Path], kind: str, when: str, message: str | None) -> int:
    current = read_version_file(p["version"])
    next_version = bump_semver(current, kind)
    return cmd_set(p, next_version, when, message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Oh-My-Research skill package versioning")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (auto-detected from script location)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="Print VERSION")
    sub.add_parser("check", help="Verify all version locations match")
    sub.add_parser("sync", help="Write VERSION into SKILL.md + marketplace.json")

    set_p = sub.add_parser("set", help="Set an explicit semver and sync")
    set_p.add_argument("version")
    set_p.add_argument("--date", default=None, help="Changelog date (YYYY-MM-DD)")
    set_p.add_argument("--message", default=None, help="One-line changelog note")

    bump_p = sub.add_parser("bump", help="Bump major|minor|patch, sync, changelog stub")
    bump_p.add_argument("kind", choices=("major", "minor", "patch"))
    bump_p.add_argument("--date", default=None)
    bump_p.add_argument("--message", default=None)

    args = parser.parse_args()
    root = (args.root or repo_root()).resolve()
    p = paths(root)
    when = args.date if hasattr(args, "date") and args.date else date.today().isoformat()

    if args.cmd == "show":
        raise SystemExit(cmd_show(p))
    if args.cmd == "check":
        raise SystemExit(cmd_check(p))
    if args.cmd == "sync":
        raise SystemExit(cmd_sync(p))
    if args.cmd == "set":
        raise SystemExit(cmd_set(p, args.version, when, args.message))
    if args.cmd == "bump":
        raise SystemExit(cmd_bump(p, args.kind, when, args.message))
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()

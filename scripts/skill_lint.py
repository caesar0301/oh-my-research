#!/usr/bin/env python3
"""Structural lint for the oh-my-research skill package Markdown tree.

This script never judges documentation content. It only enforces the
progressive-disclosure structure the skill relies on:

* SKILL.md stays a compact entry (line budget, frontmatter description limits)
* every loadable doc declares its load condition (``> Load when:``)
* long docs carry a ``## Contents`` TOC (partial-read safety)
* one H1 per doc, no heading-level skips
* every doc referenced from SKILL.md exists
* every doc under ``references/`` (+ ``scripts/README.md``) is listed in the
  ``references/REFERENCE.md`` File Index (no orphan docs)

Run from the repo root: ``python3 scripts/skill_lint.py``
Exit 0 = clean, 1 = issues found. ``--json`` emits a machine-readable report.
This is a repo-maintenance tool; it is not part of the installed skill package.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_LINE_BUDGET = 500
DESCRIPTION_LIMIT = 1024
TOC_LINE_THRESHOLD = 100
LOADWHEN = "> Load when:"
INDEX_FILE = Path("references/REFERENCE.md")
# Docs that must carry a Load when line: everything under references/, plus
# the scripts catalog. SKILL.md is the always-loaded entry; assets/ holds
# templates, not agent docs — both are exempt.
LOADWHEN_GLOBS = ("references/**/*.md", "scripts/README.md")
# Method playbooks are indexed by filename in the File Index table; every
# other doc is indexed by its skill-root-relative path.
FILENAME_INDEXED_DIR = Path("references/THINK/methods")
MD_REF_RE = re.compile(r"`((?:references|scripts|assets|patterns)/[\w./-]+\.md)`")


def default_root() -> Path:
    """Skill package root: <repo>/scripts/ → <repo>/skills/oh-my-research."""
    return Path(__file__).resolve().parents[1] / "skills" / "oh-my-research"


def doc_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in LOADWHEN_GLOBS:
        files.extend(root.glob(pattern))
    return sorted(set(files))


def split_fences(lines: list[str]) -> list[tuple[str, bool]]:
    """Pair every line with an in_fence flag (```-delimited code fences)."""
    out: list[tuple[str, bool]] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            out.append((line, True))
            in_fence = not in_fence
            continue
        out.append((line, in_fence))
    return out


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """[(line_no, level, text)] for ATX headings outside code fences."""
    found: list[tuple[int, int, str]] = []
    for no, (line, in_fence) in enumerate(split_fences(lines), start=1):
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            found.append((no, len(match.group(1)), match.group(2).strip()))
    return found


def frontmatter_description(lines: list[str]) -> str | None:
    """Extract the single-line `description:` from YAML frontmatter, if any."""
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def lint_skill_md(root: Path) -> list[dict]:
    issues: list[dict] = []
    path = root / "SKILL.md"
    if not path.exists():
        return [
            {
                "file": "SKILL.md",
                "rule": "skill_exists",
                "message": "SKILL.md is missing",
            }
        ]
    lines = path.read_text(encoding="utf-8").split("\n")
    if len(lines) > SKILL_LINE_BUDGET:
        issues.append(
            {
                "file": "SKILL.md",
                "rule": "skill_line_budget",
                "message": f"{len(lines)} lines exceeds the {SKILL_LINE_BUDGET}-line entry budget",
            }
        )
    description = frontmatter_description(lines)
    if not description:
        issues.append(
            {
                "file": "SKILL.md",
                "rule": "description_present",
                "message": "frontmatter `description:` is missing or empty",
            }
        )
    elif len(description) > DESCRIPTION_LIMIT:
        issues.append(
            {
                "file": "SKILL.md",
                "rule": "description_length",
                "message": f"description is {len(description)} chars (limit {DESCRIPTION_LIMIT})",
            }
        )
    for ref in sorted(set(MD_REF_RE.findall(path.read_text(encoding="utf-8")))):
        if not (root / ref).exists():
            issues.append(
                {
                    "file": "SKILL.md",
                    "rule": "skill_ref_exists",
                    "message": f"referenced doc does not exist: {ref}",
                }
            )
    return issues


def lint_doc(path: Path, root: Path) -> list[dict]:
    issues: list[dict] = []
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")

    h1s = [h for h in headings(lines) if h[1] == 1]
    if len(h1s) != 1:
        issues.append(
            {
                "file": rel,
                "rule": "single_h1",
                "message": f"expected exactly one H1, found {len(h1s)}",
            }
        )
    elif h1s[0][0] != 1:
        issues.append(
            {
                "file": rel,
                "rule": "h1_first_line",
                "message": f"H1 must be the first line (found at line {h1s[0][0]})",
            }
        )

    levels = [level for _, level, _ in headings(lines)]
    for prev, cur in zip(levels, levels[1:]):
        if cur > prev + 1:
            issues.append(
                {
                    "file": rel,
                    "rule": "heading_no_skip",
                    "message": f"heading level skips H{prev} → H{cur}",
                }
            )
            break

    if not any(
        line.startswith(LOADWHEN)
        for line, in_fence in split_fences(lines[:10])
        if not in_fence
    ):
        issues.append(
            {
                "file": rel,
                "rule": "load_when_present",
                "message": f"missing `{LOADWHEN} …` line within the first 10 lines",
            }
        )

    if len(lines) > TOC_LINE_THRESHOLD:
        h2s = [text for _, level, text in headings(lines) if level == 2]
        if "Contents" not in h2s:
            issues.append(
                {
                    "file": rel,
                    "rule": "toc_present",
                    "message": (
                        f"{len(lines)} lines > {TOC_LINE_THRESHOLD} but no `## Contents` TOC"
                    ),
                }
            )

    return issues


def lint_orphans(root: Path) -> list[dict]:
    issues: list[dict] = []
    index_path = root / INDEX_FILE
    if not index_path.exists():
        return [
            {
                "file": INDEX_FILE.as_posix(),
                "rule": "index_exists",
                "message": f"File Index is missing: {INDEX_FILE.as_posix()}",
            }
        ]
    index_text = index_path.read_text(encoding="utf-8")
    for path in doc_files(root):
        rel = path.relative_to(root)
        indexed = (
            rel.as_posix() in index_text
            if rel.parent != FILENAME_INDEXED_DIR
            else path.name in index_text
        )
        if not indexed:
            issues.append(
                {
                    "file": rel.as_posix(),
                    "rule": "indexed_in_reference",
                    "message": f"not listed in {INDEX_FILE.as_posix()} File Index (orphan doc)",
                }
            )
    return issues


def run(root: Path) -> dict:
    issues = lint_skill_md(root)
    for path in doc_files(root):
        issues.extend(lint_doc(path, root))
    issues.extend(lint_orphans(root))
    issues.sort(key=lambda i: (i["file"], i["rule"]))
    return {"ok": not issues, "checked": len(doc_files(root)) + 1, "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", type=Path, default=default_root(), help="skill package root"
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)

    report = run(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for issue in report["issues"]:
            print(f"{issue['file']}: [{issue['rule']}] {issue['message']}")
        verdict = "OK" if report["ok"] else "FAILED"
        print(
            f"skill-lint {verdict} — {report['checked']} doc(s) checked, "
            f"{len(report['issues'])} issue(s)"
        )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

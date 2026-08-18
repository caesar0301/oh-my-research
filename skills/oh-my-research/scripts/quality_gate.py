#!/usr/bin/env python3
"""QA1 / QA2 quality gate checks for OMR workspaces (heuristic, agent-assisted)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from export_report import validate_publication


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _glob_one(plans: Path, prefix: str) -> Path | None:
    matches = sorted(plans.glob(f"{prefix}-*.md"))
    return matches[-1] if matches else None


def _write_result(workspace: Path, name: str, result: dict[str, Any]) -> Path:
    out = workspace / ".omr" / "quality-gates" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return out


def qa1(workspace: Path) -> dict[str, Any]:
    index = workspace / "docs" / "index" / "papers-index.json"
    plans = workspace / "docs" / "plans"
    evidence = _glob_one(plans, "evidence")
    judgment = _glob_one(plans, "judgment")

    paper_count = 0
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
        if isinstance(data, list):
            paper_count = len(data)
        elif isinstance(data, dict):
            paper_count = len(data.get("papers") or data.get("items") or [])

    ev_text = _read(evidence) if evidence else ""
    ju_text = _read(judgment) if judgment else ""

    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "id": "coverage",
            "status": "pass" if paper_count >= 5 else ("warn" if paper_count >= 1 else "fail"),
            "details": f"{paper_count} indexed papers (prefer ≥5 for deep survey)",
            "metric": {"total": paper_count, "min_preferred": 5},
        }
    )
    has_gaps = bool(re.search(r"open gaps|## open gaps", ev_text, re.I))
    checks.append(
        {
            "id": "gap-detection",
            "status": "pass" if has_gaps else "fail",
            "details": "Open gaps section present" if has_gaps else "Missing Open Gaps section",
        }
    )
    has_contra = bool(re.search(r"contradiction", ju_text + ev_text, re.I))
    checks.append(
        {
            "id": "contradiction",
            "status": "pass" if has_contra else "warn",
            "details": "Contradiction section mentioned"
            if has_contra
            else "No contradiction section found — state 'None detected' explicitly",
        }
    )
    refs = set(re.findall(r"\[([PWG]-\d+)\]", ev_text + ju_text))
    checks.append(
        {
            "id": "traceability",
            "status": "pass" if refs else "fail",
            "details": f"{len(refs)} citation IDs found in evidence/judgment",
            "metric": {"ids": sorted(refs)},
        }
    )
    grades = {
        "proven": len(re.findall(r"\bproven\b", ev_text, re.I)),
        "suggests": len(re.findall(r"\bsuggests\b", ev_text, re.I)),
        "inferred": len(re.findall(r"\binferred\b", ev_text, re.I)),
    }
    grade_ok = grades["proven"] + grades["suggests"] >= 1
    checks.append(
        {
            "id": "evidence-grade",
            "status": "pass" if grade_ok else "fail",
            "details": f"grade counts={grades}",
            "metric": grades,
        }
    )

    overall = "pass"
    if any(c["status"] == "fail" for c in checks):
        overall = "fail"
    elif any(c["status"] == "warn" for c in checks):
        overall = "warn"

    result = {"gate": "QA1", "run_at": _now(), "status": overall, "checks": checks}
    _write_result(workspace, "QA1-evidence-analysis.json", result)
    return result


def qa2(workspace: Path) -> dict[str, Any]:
    docs = workspace / "docs"
    mode_dirs = [d for d in ("survey", "report", "manuscript", "brief") if (docs / d).is_dir()]
    files: list[Path] = []
    for m in mode_dirs:
        files.extend(
            sorted(
                p
                for p in (docs / m).glob("*.md")
                if p.name not in {"_export.md", "_publication.md"}
            )
        )
    text = "\n".join(_read(f) for f in files)
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "id": "structure",
            "status": "pass" if files else "fail",
            "details": f"{len(files)} markdown files in {mode_dirs}",
        }
    )
    has_limits = bool(
        re.search(r"limitation|open gaps|gaps and limitations|研究局限|局限性|研究空白", text, re.I)
    )
    checks.append(
        {
            "id": "coherence",
            "status": "pass" if has_limits else "fail",
            "details": "Limitations/gaps section found" if has_limits else "Missing limitations/gaps",
        }
    )
    numbered_refs = set(re.findall(r"\[(\d{1,4})\]", text))
    author_date_refs = set(
        re.findall(r"[\(（][^()（）\n]{1,80}[,，]\s*(?:19|20)\d{2}[a-z]?[\)）]", text)
    )
    reference_count = len(numbered_refs) + len(author_date_refs)
    checks.append(
        {
            "id": "citations",
            "status": "pass" if reference_count else "warn",
            "details": f"{reference_count} reader-facing citation markers in synthesis",
            "metric": {
                "numbered": len(numbered_refs),
                "author_date": len(author_date_refs),
            },
        }
    )
    private_terms = validate_publication(text)
    checks.append(
        {
            "id": "publication-safety",
            "status": "pass" if not private_terms else "fail",
            "details": (
                "No private workflow terminology found"
                if not private_terms
                else f"{len(private_terms)} private reference/term finding(s)"
            ),
            "findings": private_terms[:30],
        }
    )
    section_terms = (
        "executive summary",
        "摘要",
        "findings",
        "研究发现",
        "limitations",
        "局限",
        "references",
        "参考文献",
    )
    section_hits = sum(1 for term in section_terms if term.lower() in text.lower())
    checks.append(
        {
            "id": "self-contained",
            "status": "pass" if section_hits >= 3 else "warn",
            "details": f"{section_hits} expected reader-facing section signals found",
        }
    )
    deliverables: list[Path] = []
    for mode in mode_dirs:
        deliverable_dir = docs / mode / "deliverables"
        if deliverable_dir.is_dir():
            deliverables.extend(deliverable_dir.glob("*.docx"))
            deliverables.extend(deliverable_dir.glob("*.pdf"))
    checks.append(
        {
            "id": "rendering",
            "status": "pass" if deliverables and all(p.stat().st_size > 1000 for p in deliverables) else "warn",
            "details": (
                f"{len(deliverables)} non-empty DOCX/PDF deliverable(s) found"
                if deliverables
                else "No rendered DOCX/PDF found; export and inspect before publication"
            ),
            "files": [str(p.relative_to(workspace)) for p in deliverables],
        }
    )
    overall = "pass"
    if any(c["status"] == "fail" for c in checks):
        overall = "fail"
    elif any(c["status"] == "warn" for c in checks):
        overall = "warn"
    result = {"gate": "QA2", "run_at": _now(), "status": overall, "checks": checks}
    _write_result(workspace, "QA2-pre-export.json", result)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="OMR quality gates")
    p.add_argument("gate", choices=["qa1", "qa2", "all"])
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    args = p.parse_args()
    ws = args.workspace.resolve()
    results = []
    if args.gate in ("qa1", "all"):
        results.append(qa1(ws))
    if args.gate in ("qa2", "all"):
        results.append(qa2(ws))
    print(json.dumps(results if len(results) > 1 else results[0], indent=2))


if __name__ == "__main__":
    main()

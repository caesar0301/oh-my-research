# Oh-My-Research — Complete Reference

Detailed operation guide for the unified OMR skill.

## Operations Index

| Mode | Ops | Reference |
|------|-----|-----------|
| INIT | `init` | `INIT/init.md` |
| COLLECT | `collect` | `COLLECT/collect.md` |
| ANALYZE | `analyze` | `ANALYZE/analyze.md` |
| THINK | `think [method]` | `THINK/think.md`, `THINK/methods.md` |
| SYNTH | `synth [--mode] [--format] [--language] [--resume] [--chapter] [--no-wiki]` | `SYNTH/synth.md`, `SYNTH/long-report.md` |
| QA | `qa qa1\|qa2\|all` | `GATES.md`, `LLM-STATE.md` |
| IDEA | `idea` | `IDEA/idea.md` |
| DECIDE | `decide` | `DECIDE/decide.md` |
| RECONCILE | `reconcile`, `archive`, `rollback`, `list` | `RECONCILE/reconcile.md` |
| VERSION | `version tag\|history\|diff\|backup\|list` (workspace); `skill-version show\|check\|sync\|set\|bump` (package) | `VERSION/version.md` |
| WORKFLOW | `workflow [--phase N] [--pattern P]` | `WORKFLOW/workflow-overview.md` |

Cross-cutting: `GATES.md`, `GRAPH.md`, `LLM-STATE.md`.

---

## Auto-Detection Decision Tree

```
Canonical op name in request?
  → Yes → run that op (wins)

skill-version / bump skill / skill changelog / release skill?
  → VERSION skill-package track (`skill_version.py`)

version tag|history|diff|backup|list?
  → VERSION workspace track (`version_control.py`)

THINK keywords? (first principles, socratic, pre-mortem, red team,
                 steelman, deepen, rethink, elicit, think)
  → THINK on latest research artifact (or user-pointed path)

IDEA keywords? (idea, brainstorm, speculate, what if, hypothesis)
  → IDEA mode

COLLECT signals? (URL, DOI, arxiv, github.com, huggingface, "search …", collect)
  → COLLECT (init-on-demand if no AGENTS.md / .omr/)

SYNTH keywords? (report, survey, write up, synthesize, manuscript, brief)
  → SYNTH mode

Else inspect workspace:

No AGENTS.md AND no .omr/ ?
  → INIT

Materials or papers-index, no judgment-* ?
  → ANALYZE (default) — unless user clearly still adding sources → COLLECT

Judgment present, no docs/{survey,report,manuscript,brief}/ content ?
  → SYNTH

loop-state active ?
  → Gate L (iterate vs advance) before next unlock

Contradiction vs published claims/decision ?
  → propose RECONCILE

Ambiguous ?
  → Ask user OR show graph-recommended next from Evidence-Deep
```

---

## Artifact Naming

| Artifact | Pattern | Location |
|----------|---------|----------|
| Research brief | `brief-{id}.md` | `docs/plans/` |
| Evidence map | `evidence-{id}.md` | `docs/plans/` |
| Judgment | `judgment-{id}.md` | `docs/plans/` |
| Research plan | `plan-{id}.md` | `docs/plans/` |
| Decision (optional) | `decision-DEC-{nnn}.md` | `docs/plans/` |
| Idea note | `YYYY-MM-DD-<slug>.md` | `docs/ideas/` |
| Papers index | `papers-index.json` (+ `.md`) | `docs/index/` |
| Synthesis | chapters under mode dir | `docs/{survey,report,manuscript,brief}/` |
| Material IDs | `P-xxx` papers, `W-xxx` web, `G-xxx` github | indexes |

`{id}` default: `R-001` for first research thread (increment if multiple threads).

**Layout rule:** locations above are destinations for real files. Never create those directories empty — write the file (parent dirs appear as a side effect). INIT only creates `AGENTS.md` + `.omr/*.json`. See `INIT/init.md`.

---

## Evidence Boundaries (non-negotiable)

| Level | Label | Meaning |
|-------|-------|---------|
| **proven** | "Paper X validates / proves…" | Strong experimental or formal validation in source |
| **suggests** | "Paper X suggests / demonstrates…" | Indirect or limited evidence |
| **inferred** | "Based on X, we infer…" | Multi-source synthesis; explicit boundary |
| **speculative** | — | Exclude from evidence map as anchor |

Never claim "proves" when authors only suggest or demonstrate.

---

## Tree State

File: `.omr/tree-state.json`

```json
{
  "unlocked": ["init", "collect", "idea", "think"],
  "ready": ["analyze"],
  "locked": ["synth", "decide", "reconcile"],
  "completed": []
}
```

Update after each op using graph rules in `GRAPH.md` (LLM edits `.omr/tree-state.json` — see `LLM-STATE.md`).

---

## Template Variables

Templates use `{{PLACEHOLDER}}` syntax:

- `{{PROJECT_NAME}}`, `{{RESEARCH_QUESTION}}`, `{{TOPIC}}`
- `{{DATE}}`, `{{AUTHOR}}`
- `{{ACTIVE_PATTERN}}`, `{{STATUS}}`
- `{{BRIEF_ID}}`, `{{EVIDENCE_ID}}`, `{{JUDGMENT_ID}}`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Wrong auto-detection | Use explicit op (`analyze`, `synth`, `think first-principles`) |
| Gate A fails | Collect more materials or run THINK (triangulation / first principles) |
| Shallow judgment | `think` with Literature Review Personas or Thesis Defense |
| Over-claiming in draft | Lenses + Gate D; fix evidence boundaries |
| Missing citations | Ensure every claim has `[P-xxx]` / `[W-xxx]` linked in index |
| Stuck after collect | Run `analyze` |

---

## Reference Map

- `GATES.md` — A / B / D / L / QA1 / QA2 / lenses (LLM-evaluated)
- `LLM-STATE.md` — agent-owned state JSON; scripts only for render/backup/optional collect
- `GRAPH.md` — pattern graphs and next-step routing
- `THINK/` — elicitation behavior + method catalog
- `ANALYZE/` — deep analysis pipeline
- `SYNTH/` — incremental long-report protocol + export
- `WORKFLOW/` — end-to-end Evidence-Deep
- `patterns/*.json` — machine-readable graphs

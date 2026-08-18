---
name: oh-my-research
description: Intelligent orchestrator for high-quality deep research reports from collected materials and evidence. Auto-detects intent and workspace state, then routes to init, collect, deep analyze (with THINK paradigms such as first principles), optional decide/idea, synthesize survey/report, reconcile, or version. Single entry point for the report-first research lifecycle.
license: Apache-2.0
metadata:
  version: "1.0.0"
  author: "Xiaming Chen"
  category: "workflow"
---

# Oh-My-Research

Intelligent orchestrator for **report-first deep research**. Auto-detects user intent and workspace state, then executes the right mode—initialize, collect materials, deep-analyze with evidence boundaries and thinking paradigms, synthesize a survey/report, or maintain state.

**North star:** high-quality deep research reports from collected materials and evidence — not prototypes, not coding validation.

## When to Use This Skill

- **Start** a research workspace on a topic
- **Collect** papers, URLs, repos, datasets
- **Analyze** materials into evidence maps and judgments
- **Deepen** analysis with first principles, Socratic, triangulation, etc. (THINK)
- **Write** a survey, report, manuscript, or brief
- **Reconcile** when new evidence contradicts prior claims
- **Run** the full Evidence-Deep workflow

**Keywords**: research, survey, literature review, evidence, collect papers, analyze, first principles, synthesize report, deep research, oh-my-research, omr

## Intelligent Auto-Detection

See `references/REFERENCE.md` for the full decision tree.

### Intention Detection (runs first)

Before inspecting workspace state, scan the request:

| Signal (case-insensitive) | Route |
|---------------------------|-------|
| `first principles`, `socratic`, `pre-mortem`, `red team`, `steelman`, `deepen`, `rethink`, `elicit`, `think` | **THINK** on latest artifact |
| `idea`, `brainstorm`, `speculate`, `what if`, `hypothesis` | **IDEA** |
| URL / DOI / arxiv / GitHub / HuggingFace / `search …` / `collect` | **COLLECT** (init-on-demand if needed) |
| `report`, `survey`, `write up`, `synthesize`, `manuscript`, `brief` | **SYNTH** |
| Canonical op (`init`, `collect`, `analyze`, `think`, `synth`, `decide`, `idea`, `reconcile`, `workflow`, `qa`, `version`) | Named mode — **wins** over keyword routing |

### Workspace-State Detection (when no strong intent)

1. No `AGENTS.md` and no `.omr/` → **INIT**
2. Materials / `papers-index` present, no `docs/plans/judgment-*` → **ANALYZE** (prefer deepen; COLLECT only if user is still adding sources)
3. Judgment present, no synthesis under `docs/{survey,report,manuscript,brief}/` → **SYNTH**
4. Active `.omr/loop-state.json` with `active: true` → surface **Gate L** before advancing
5. New materials contradict published claims / decision → propose **RECONCILE**
6. Ambiguous → ask or show graph-recommended next step

**Override** with canonical operations at any time.

Always show a phase label: `[INIT]`, `[COLLECT]`, `[ANALYZE]`, `[THINK]`, `[SYNTH]`, `[RECONCILE]`, `[FINISHED]` (plus `[DECIDE]` / `[IDEA]` when used).

## Core Pipeline (Evidence-Deep)

```
COLLECT materials → ANALYZE (deep evidence + THINK) → SYNTH (survey / report)
```

Optional: IDEA, DECIDE (stance), RECONCILE, VERSION.

Default pattern: **Evidence-Deep**. See `references/GRAPH.md` and `patterns/`.

## Operation Modes

### INIT Mode
Bootstrap workspace. Op: `init "<topic>"`. Creates `AGENTS.md` + `.omr/tree-state.json`. Content dirs on demand. → `references/INIT/init.md`

### COLLECT Mode
Passive reception of sources → materials + indexes. Op: `collect <url|query|…>`. → `references/COLLECT/collect.md`

### ANALYZE Mode
Deep analysis centerpiece: brief, evidence-map, judgment, optional plan; Gate A / QA1; THINK checkpoint. Op: `analyze`. → `references/ANALYZE/analyze.md`

### THINK Mode
Structured elicitation on research artifacts (never code). Op: `think [method]`. → `references/THINK/think.md`

### SYNTH Mode
Primary deliverable: long, publication-quality English or Chinese Word/PDF reports written **incrementally** (outline → one chapter per turn → continuity brief → assemble). Ops: `synth [--mode] [--format docx|pdf] [--language en|zh-CN] [--resume] [--chapter <id>] [--no-wiki]`. Never generate an entire deep report in one turn. Public deliverables must be self-contained and must not expose workflow terms, internal material IDs, evidence-grade labels, or artifact paths. → `references/SYNTH/synth.md` and `references/SYNTH/long-report.md`

### IDEA Mode (optional)
Capture speculative notes. Op: `idea "…"`. → `references/IDEA/idea.md`

### DECIDE Mode (optional)
Stance / claim framing with ≥3 alternatives; Gate B. Op: `decide`. → `references/DECIDE/decide.md`

### RECONCILE Mode
Contradiction blast-radius, archive, rollback. → `references/RECONCILE/reconcile.md`

### VERSION Mode
Tag / history / diff / backup / list. → `references/VERSION/version.md`

### WORKFLOW Mode
Graph-driven multi-step Evidence-Deep (or other pattern). Op: `workflow [--pattern P]`. → `references/WORKFLOW/workflow-overview.md`

### QA
`qa qa1|qa2|all` — see `references/GATES.md`.

## Confirmation Gates

Default **semi-automated** (pause for confirm). Support “no confirmations” / quick-pass.

| Gate | When |
|------|------|
| L | Loop pattern: iterate vs advance |
| A / QA1 | After ANALYZE judgment, before unlock SYNTH |
| B | Only if DECIDE runs |
| Lenses | Structure → Prose → Adversarial before Gate D |
| D / QA2 | Before publishing SYNTH |

No Gate C / no evaluation path.

## Post-Step Routing Menu

After IDEA / Gate A / THINK proceed / Gate B:

1. **Pause at each gate** (default)
2. **Quick pass** — continue without further confirmations
3. **Continue recommended** — next graph edge
4. **Run THINK** — deepen current artifact
5. **Switch pattern**
6. **Stop**

## Default Paths

| Artifact | Path |
|----------|------|
| State | `.omr/` |
| Materials | `materials/{papers,web,github,datasets,search,failed}/` |
| Indexes | `docs/index/` |
| Plans | `docs/plans/` (brief, evidence-map, judgment, plan, optional decision) |
| Ideas | `docs/ideas/` |
| Reports | `docs/{survey,report,manuscript,brief}/` |
| Wiki | `wiki/` |
| Archive | `docs/archive/` |

Templates: `assets/`. Patterns: `patterns/`. Detailed ops: `references/REFERENCE.md`.

## Best Practices

1. Trust auto-detection; override with canonical ops when needed
2. Never upgrade `suggests` → `proven` without stronger source language
3. Use THINK (first principles / triangulation) before Gate A when confidence is low
4. Write long reports chapter-by-chapter to disk; keep a pruned continuity brief; author `.omr/report-state.json` to match the topic outline; resume if interrupted
5. Prefer a professionally formatted DOCX or PDF in the user's requested English or Chinese; drive its presentation via an LLM-authored `_document.json` (title, fonts, cover, TOC, header/footer, chapter order) rather than script defaults
6. Keep internal traceability private; translate it into standard citations and natural prose
7. Make the final report self-contained, professional, and accessible to its intended reader
8. Run LLM QA checklists (adapt thresholds to the scenario); write results under `.omr/quality-gates/`
9. Write full reports to disk; reply in chat with summary only
10. Run document lenses and visually inspect the rendered file before Gate D

## Dependencies

- Read/write project workspace
- Agent-authored state under `.omr/` (tree, loop, report-state, quality-gates) — see `references/LLM-STATE.md`
- Mechanical scripts only: `export_report.py` (thin, spec-driven DOCX/PDF renderer applying LLM-authored `_document.json`), `version_control.py` (tags/backups), optional `collect_cli.py`
- `python-docx` / `reportlab` via `scripts/requirements.txt` for export

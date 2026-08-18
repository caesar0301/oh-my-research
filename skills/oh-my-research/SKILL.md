---
name: oh-my-research
description: Intelligent orchestrator for high-quality deep research reports from collected materials and evidence. Auto-detects intent and workspace state, then routes to init, collect, deep analyze (with THINK paradigms such as first principles), optional decide/idea, synthesize survey/report, reconcile, or version. Single entry point for the report-first research lifecycle.
license: Apache-2.0
metadata:
  version: "1.1.3"
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
| Canonical op (`init`, `collect`, `analyze`, `think`, `synth`, `decide`, `idea`, `reconcile`, `workflow`, `qa`, `version`, `skill-version`) | Named mode — **wins** over keyword routing |

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

Optional: IDEA, DECIDE (stance), RECONCILE, VERSION (workspace), skill-version (package).

Default pattern: **Evidence-Deep**. See `references/GRAPH.md` and `patterns/`.

## Operation Modes

### INIT Mode
Bootstrap workspace. Op: `init "<topic>"`. Creates **only** `AGENTS.md` + `.omr/tree-state.json` + `.omr/pattern.json` + `.omr/locale.json` (language from timezone). **No empty folders** — every other path is created on first content write. → `references/INIT/init.md`

### COLLECT Mode
Passive reception of sources → materials + indexes. Op: `collect <url|query|…>`. → `references/COLLECT/collect.md`

### ANALYZE Mode
Deep analysis centerpiece: brief, evidence-map, judgment, optional plan; Gate A / QA1; THINK checkpoint. Op: `analyze`. → `references/ANALYZE/analyze.md`

### THINK Mode
Structured elicitation on research artifacts (never code). Op: `think [method]`. → `references/THINK/think.md`

### SYNTH Mode
Primary deliverable: long, publication-quality reports in the preferred language (auto-detected from timezone/locale — `en`, `zh-CN`, `ja`, `de`, … — or explicit `--language`) as Word/PDF, written **incrementally** (outline → one chapter per turn → continuity brief → assemble). Ops: `synth [--mode] [--format docx|pdf] [--language <tag>] [--resume] [--chapter <id>] [--no-wiki]`. Never generate an entire deep report in one turn. Public deliverables must be self-contained and must not expose workflow terms, internal material IDs, evidence-grade labels, or artifact paths. → `references/SYNTH/synth.md`, `references/SYNTH/long-report.md`, `references/LANGUAGE.md`

### IDEA Mode (optional)
Capture speculative notes. Op: `idea "…"`. → `references/IDEA/idea.md`

### DECIDE Mode (optional)
Stance / claim framing with ≥3 alternatives; Gate B. Op: `decide`. → `references/DECIDE/decide.md`

### RECONCILE Mode
Contradiction blast-radius, archive, rollback. → `references/RECONCILE/reconcile.md`

### VERSION Mode
Two tracks → `references/VERSION/version.md`:
- **Workspace:** `version tag|history|diff|backup|list` (research artifacts)
- **Skill package:** `skill-version show|check|sync|set|bump` (semver + `CHANGELOG.md`; source of truth `VERSION`)

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

Paths below are **logical destinations**. Create a folder only when writing the first file into it (see `references/INIT/init.md`).

| Artifact | Path (when content exists) |
|----------|------|
| State | `.omr/` (tree-state, pattern, locale; other JSON as needed) |
| Materials | `materials/{papers,web,github,datasets,search,failed}/` — only buckets that receive files |
| Indexes | `docs/index/` |
| Plans | `docs/plans/` |
| Ideas | `docs/ideas/` |
| Reports | `docs/{survey,report,manuscript,brief}/` |
| Wiki | `wiki/` |
| Archive | `docs/archive/` |

Templates: `assets/`. Patterns: `patterns/`. Detailed ops: `references/REFERENCE.md`.

## Best Practices

1. Trust auto-detection; override with canonical ops when needed
2. Never create empty directories — mkdir only as the parent of a real file write
3. Never upgrade `suggests` → `proven` without stronger source language
4. Use THINK (first principles / triangulation) before Gate A when confidence is low
5. Write long reports chapter-by-chapter to disk; keep a pruned continuity brief; author `.omr/report-state.json` to match the topic outline; resume if interrupted
6. Prefer a professionally formatted DOCX or PDF in the preferred language (timezone/locale auto-detect via `LANGUAGE.md` / `.omr/locale.json`, or explicit `--language`); drive its presentation via an LLM-authored `_document.json` (title, fonts, cover, TOC, header/footer, chapter order) rather than script defaults
7. Keep internal traceability private; translate it into standard citations and natural prose
8. Make the final report self-contained, professional, and accessible to its intended reader
9. Run LLM QA checklists (adapt thresholds to the scenario); write results under `.omr/quality-gates/`
10. Write full reports to disk; reply in chat with summary only
11. Run document lenses and visually inspect the rendered file before Gate D

## Dependencies

- Read/write project workspace
- Agent-authored state under `.omr/` (tree, loop, report-state, quality-gates) — see `references/LLM-STATE.md`
- Mechanical scripts only: `export_report.py` (thin, spec-driven DOCX/PDF renderer applying LLM-authored `_document.json`), `prefer_language.py` (timezone/locale → BCP-47 language tag), `version_control.py` (workspace tags/backups), `skill_version.py` (package semver sync), optional `collect_cli.py`
- `python-docx` / `reportlab` via `scripts/requirements.txt` for export

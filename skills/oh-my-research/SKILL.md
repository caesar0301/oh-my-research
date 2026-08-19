---
name: oh-my-research
description: Intelligent orchestrator for high-quality deep research reports from collected materials and evidence. Auto-detects intent and workspace state, then routes to init, collect, deep analyze (with THINK paradigms such as first principles), optional decide/idea, synthesize survey/report, reconcile, or version. Single entry point for the report-first research lifecycle.
license: Apache-2.0
metadata:
  version: "1.4.0"
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

### Phase-Guard: Cross-Stage Jump Protection (v1.3+, hardened in v1.4)

When auto-detection routes to a stage, **first** read `.omr/tree-state.json` and check whether the target stage is in `unlocked`, `ready`, or `completed`. If the stage is `locked`, the agent must check whether required **prerequisite artifacts** exist on disk before proceeding. This prevents silent stage-skipping (e.g. user says "write report" → SYNTH keyword detected → but no `judgment-*.md` exists).

**Prerequisite artifact checks (Evidence-Deep pattern):**

| Target stage | Required prerequisite artifacts | Required gate JSON | If missing |
|---|---|---|---|
| ANALYZE | `materials/` with ≥1 source + `docs/index/` entry | `gate-m.json` (run during ANALYZE) | Route to COLLECT first |
| THINK | `docs/plans/judgment-*.md` or `docs/plans/evidence-*.md` | (none) | Route to ANALYZE first |
| SYNTH | `docs/plans/judgment-*.md` | `gate-a.json` (pass) + `gate-p.json` | Route to ANALYZE → THINK → Gate A → Gate P first |
| DECIDE | `docs/plans/judgment-*.md` | (none) | Route to ANALYZE first |

**Enforcement protocol (v1.4 — blocking by default):**

1. Before executing a stage, read `.omr/tree-state.json` and check if the stage is in `unlocked`, `ready`, or `completed`.
2. If the stage is `locked`, check if the required artifacts **and gate JSON** exist on disk.
3. If artifacts exist but tree-state is stale → update tree-state and proceed.
4. If artifacts are missing → **BLOCK**: show `[PHASE-GUARD]` notice with the specific missing prerequisites and offer to run the prerequisite stage. **Do not proceed until the user explicitly overrides** (e.g. types "I know, just write the report" or "skip guard").
5. If user explicitly overrides, proceed but record `scenario_note: "prerequisite skipped by user override"` in the next gate JSON.

**Blocking vs advisory (v1.4 change):** In v1.3 the guard was "advisory, not blocking." Real-world usage showed this was too soft — agents routinely skipped the guard entirely. In v1.4 the guard is **blocking by default**: the agent must not proceed to a locked stage without either (a) satisfying the prerequisites or (b) receiving an explicit user override. The override must be recorded in the gate JSON for auditability.

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
Passive reception of sources → materials + indexes + **full-text Markdown**. Each source is downloaded and converted to `materials/<bucket>/<ID>.md` via **anydoc** (with fallbacks), so ANALYZE can read the entire paper — not just the abstract. Op: `collect <url|query|…>`. → `references/COLLECT/collect.md`

### ANALYZE Mode
Deep analysis centerpiece: brief, evidence-map, judgment, optional plan. **Reads full-text Markdown** (`materials/<bucket>/<ID>.md`) for each material — abstract-only is a degraded fallback, not the default. Guarded by **Gate M** (enough materials + full-text available?) before, **Gate A / QA1** after, and **Gate T** (collect more?) after a THINK pass. Op: `analyze`. → `references/ANALYZE/analyze.md`

### THINK Mode
Methodology-driven elicitation on research artifacts (never code). Each pass loads a playbook (`references/THINK/methods/<slug>.md`), never default-agrees, and stamps an outcome (`hardened`/`refined`/`unchanged`/`killed`). Op: `think [method]`. → `references/THINK/think.md`, `references/THINK/methods/`

### SYNTH Mode
Primary deliverable: long, publication-quality reports in the preferred language (auto-detected from timezone/locale — `en`, `zh-CN`, `ja`, `de`, … — or explicit `--language`) as Word/PDF, written **incrementally** (outline → one chapter per turn → continuity brief → assemble). **Gate P** confirms language / format / mode / audience / citations before writing. Ops: `synth [--mode] [--format docx|pdf] [--language <tag>] [--resume] [--chapter <id>] [--no-wiki]`. Never generate an entire deep report in one turn. Public deliverables must be self-contained and must not expose workflow terms, internal material IDs, evidence-grade labels, or artifact paths. → `references/SYNTH/synth.md`, `references/SYNTH/long-report.md`, `references/LANGUAGE.md`

### IDEA Mode (optional)
Capture speculative notes. Op: `idea "…"`. → `references/IDEA/idea.md`

### DECIDE Mode (optional)
Stance / claim framing with ≥3 alternatives; Gate B. Op: `decide`. → `references/DECIDE/decide.md`

### RECONCILE Mode
Contradiction blast-radius, archive, rollback. → `references/RECONCILE/reconcile.md`

### VERSION Mode
Two tracks → `references/VERSION/version.md`:
- **Workspace:** `version tag|history|diff|backup|list` (research artifacts)
- **Skill package:** `skill-version show|check|sync|set|bump` (semver + `CHANGELOG.md`; source of truth `SKILL.md` → `metadata.version`)

### WORKFLOW Mode
Graph-driven multi-step Evidence-Deep (or other pattern). Op: `workflow [--pattern P]`. → `references/WORKFLOW/workflow-overview.md`

### QA
`qa qa1|qa2|all|state-check` — see `references/GATES.md`. `state-check` (v1.4) runs disk-vs-tree-state reconciliation: scans disk for actual artifacts, compares against `.omr/tree-state.json`, proposes corrections, and lists missing gates/artifacts.

## Confirmation Gates

Default **semi-automated** (pause for confirm). Support “no confirmations” / quick-pass.

| Gate | When |
|------|------|
| M | After COLLECT: enough materials to analyze? |
| L | Loop pattern: iterate vs advance |
| A / QA1 | After ANALYZE judgment, before unlock SYNTH |
| T | After THINK: collect more from surfaced gaps? |
| B | Only if DECIDE runs |
| P | Before SYNTH: language / format / mode / audience |
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
2. **Phase-Guard before every stage (blocking by default)**: read `.omr/tree-state.json`, run startup reconciliation (disk vs. state), check prerequisites, show `[PHASE-GUARD]` if missing — **block** unless user explicitly overrides with override language. Never silently skip a stage
3. Never create empty directories — mkdir only as the parent of a real file write
4. Never upgrade `suggests` → `proven` without stronger source language
5. Use THINK (first principles / triangulation) before Gate A when confidence is low — **in Evidence-Deep pattern, THINK is offered by default after judgment, not only when confidence is low**
6. Write long reports chapter-by-chapter to disk; keep a pruned continuity brief; author `.omr/report-state.json` to match the topic outline; resume if interrupted
7. Prefer a professionally formatted DOCX or PDF in the preferred language (timezone/locale auto-detect via `LANGUAGE.md` / `.omr/locale.json`, or explicit `--language`); drive its presentation via an LLM-authored `_document.json` (title, fonts, cover, TOC, header/footer, chapter order) rather than script defaults
8. Keep internal traceability private; translate it into standard citations and natural prose
9. Make the final report self-contained, professional, and accessible to its intended reader
10. Run LLM QA checklists (adapt thresholds to the scenario); write results under `.omr/quality-gates/`
11. Write full reports to disk; reply in chat with summary only
12. Run document lenses and visually inspect the rendered file before Gate D
13. **Update `.omr/tree-state.json` after every op** — move completed stages to `completed`, unlock next stages; never leave tree-state stale

## Dependencies

- Read/write project workspace
- Agent-authored state under `.omr/` (tree, loop, report-state, quality-gates) — see `references/LLM-STATE.md`
- Mechanical scripts only: `export_report.py` (thin, spec-driven DOCX/PDF renderer applying LLM-authored `_document.json`), `prefer_language.py` (timezone/locale → BCP-47 language tag), `version_control.py` (workspace tags/backups), `skill_version.py` (package semver sync), `collect_cli.py` (records source + invokes `material_to_markdown.py` to download + convert to full-text Markdown), `material_to_markdown.py` (downloads source via arxiv/DOI/URL, converts to Markdown via **anydoc** with pymupdf/pdfplumber/markdownify fallbacks; supports `--convert-dir` for batch conversion of pre-downloaded files), `report_lint.py` (publication-safety linter: scans report chapters for leaked internal IDs, evidence-grade labels, workflow jargon, gate names, and private paths)
- `python-docx` / `reportlab` via `scripts/requirements.txt` for export; **anydoc** (`npx -y @firecrawl/anydoc`, Node 20+) for material → Markdown conversion; optional `pymupdf` / `pdfplumber` / `markdownify` / `beautifulsoup4` as fallbacks if anydoc is unavailable

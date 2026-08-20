# Quality Gates (Report-First)

Gates are **LLM-evaluated**. The agent reads artifacts, applies the checklists below with scenario judgment, writes results under `.omr/quality-gates/`, and asks the user to confirm (unless quick-pass). See also `LLM-STATE.md`.

## Overview

| Gate | Position | Purpose | Required artifacts |
|------|----------|---------|-------------------|
| **M** | After COLLECT, before ANALYZE | Source diversity & enough materials? | materials + index |
| **L** | IDEA / ANALYZE when Loop active | Iterate deeper or advance? | `.omr/loop-state.json` |
| **A** | After ANALYZE judgment, before unlock SYNTH | Evidence sufficient for report? | brief, evidence-map, judgment |
| **QA1** | After judgment (auto or `qa qa1`) | Coverage, gaps, traceability | papers-index, evidence, judgment |
| **T** | After a THINK pass | Material gaps surfaced by THINK → collect more? | think revelations / collect-targets |
| **B** | Only if DECIDE runs | Stance sound? | decision draft (≥3 alts, risks, refs) |
| **P** | After Gate A, before SYNTH outline | Language, format, mode, audience, citations | judgment + preferences |
| **Lenses** | Before Gate D on SYNTH draft | Structure / Prose / Adversarial | `docs/<mode>/chapters/` |
| **D** | Before publishing SYNTH | Traceable, no over-claiming? | judgment (+ optional decision) |
| **QA2** | Pre-export (`qa qa2`) | Structure, citations, coherence, safety | chapters + deliverable |

**Removed:** Gate C and experiment-design checks. **No quality-gate Python runner** — judgment is agent-side.

## Gate Chain Enforcement (v1.4 — self-enforcing chain)

Gates form a **chain** — each gate depends on the previous one. The agent must not skip gates in the chain, even when the user gives a task-oriented instruction that seems to bypass the workflow.

**Evidence-Deep gate chain (mandatory order):**

```
Gate M → [ANALYZE] → THINK pass → Gate T → Gate A/QA1 → Gate P → [SYNTH] → Lenses → Gate D/QA2
```

**Rules:**

1. **Each gate must be recorded as JSON** under `.omr/quality-gates/` before the next stage starts. A missing gate JSON file means the gate was not run.
2. **Gate A checks for THINK**: if pattern is Evidence-Deep, Gate A verifies that at least one THINK pass is recorded in the judgment's THINK ledger. If not, Gate A fails.
3. **Gate P checks for Gate A**: Gate P verifies that `gate-a.json` exists and has `status: "pass"`. If not, Gate P refuses to proceed.
4. **SYNTH checks for Gate P**: SYNTH verifies that `gate-p.json` exists before starting the outline. If not, SYNTH runs Gate P first.
5. **Gate D checks for Gate P + Lenses**: Gate D verifies that `gate-p.json` exists and lenses were run. If not, Gate D fails.

**Gate chain completeness check (v1.4 — self-enforcing):**

Before recording any gate X, the agent must verify that all prerequisite gates in the chain have been recorded. This makes the chain self-enforcing: a missing prerequisite gate blocks the current gate from being recorded.

**Prerequisite matrix (gate-level):**

| Gate being recorded | Required prerequisite gate JSONs | If missing |
|---|---|---|
| `gate-t.json` | `gate-m.json` (or retroactively recorded) | **Refuse** — run Gate M first |
| `gate-a.json` | `gate-m.json` + `gate-t.json` | **Refuse** — run Gate T first (or record retroactively if THINK was done) |
| `gate-p.json` | `gate-a.json` with `status: "pass"` | **Refuse** — Gate A must pass first |
| `gate-d.json` | `gate-p.json` + evidence of lenses run | **Refuse** — run Gate P + lenses first |

**Enforcement protocol:**

1. Before writing a gate JSON, check that all prerequisite gate JSONs exist under `.omr/quality-gates/`
2. If a prerequisite is missing:
   - If the corresponding work was actually done (e.g. THINK was run but Gate T wasn't recorded) → record the missing gate retroactively with `scenario_note: "retroactively recorded"`, then proceed
   - If the work was genuinely not done → **refuse to record the current gate** and direct the agent to run the missing gate first
3. If the user explicitly overrides (override language required) → record `scenario_note: "gate chain prerequisite skipped by user override"` in the current gate JSON, but the chain gap must be acknowledged

This prevents the common failure mode where an agent skips multiple gates and then tries to record only the final gate, leaving the chain broken.

**Cross-stage jump detection:**

If the agent detects that the user wants to jump from COLLECT directly to SYNTH (e.g. "write the report"), it must:
1. Show a `[PHASE-GUARD]` notice: "ANALYZE + THINK + Gate A have not been run. Proceeding to SYNTH without these stages may produce a report with insufficient evidence depth."
2. Offer to run the prerequisite stages automatically
3. If user insists, proceed but record `scenario_note: "cross-stage jump: collect → synth (prerequisites skipped by user override)"` in `gate-p.json`

## Enforcement Modes

| Mode | Behavior |
|------|----------|
| **Semi-automated** (default) | User confirms at each gate |
| **Quick-pass / no confirmations** | Agent still runs checks and records JSON; skips user pause |
| **Fully-automated** | Same as quick-pass |

## How to record a gate/QA result

Write JSON (not a fixed script schema beyond this shape):

```json
{
  "gate": "QA1",
  "run_at": "ISO-8601",
  "status": "pass|warn|fail",
  "scenario_note": "e.g. narrow 4-paper deep dive — coverage bar lowered deliberately",
  "checks": [
    {
      "id": "coverage",
      "status": "pass|warn|fail",
      "details": "human-readable rationale tied to this topic"
    }
  ]
}
```

Paths: `.omr/quality-gates/QA1-evidence-analysis.json`, `QA2-pre-export.json`, or `gate-a.json`, etc.

---

## Gate M — Materials Sufficiency & Source Diversity (before ANALYZE)

Position: after COLLECT has ≥1 usable source and `analyze` is marked ready; before ANALYZE's deep pipeline begins.

**Purpose:** prevent premature analysis on a narrow or single-type corpus. Ensures the user has been offered the chance to diversify source types before committing to deep analysis.

**Checks (interpret for the intended scope — not a fixed quota):**
- [ ] **Minimum count**: ≥3 materials collected (or explicit narrow-scope note accepted)
- [ ] **Source-type diversity**: at least 2 distinct buckets populated among:
  - `papers/` (arXiv, DOI, PDFs — primary sources)
  - `web/` (blog posts, survey articles, documentation)
  - `github/` (source repos, code samples)
  - `datasets/` or HuggingFace models (benchmarks, weights, datasets)
  - Platform-specific models (DashScope, OpenAI, Anthropic — if relevant to topic)
- [ ] **Topic coverage**: collected materials touch ≥2 of the research sub-questions (from `AGENTS.md` or inferred)
- [ ] **Recency**: at least 1 source from the last 2 years (or topic-appropriate rationale)
- [ ] **Obvious gaps**: no entire sub-question area is empty of sources
- [ ] Material set matches the intended scope (narrow single-paper deep dive vs broad survey)
- [ ] At least one primary source, or an explicit plan to analyze a deliberately small corpus
- [ ] Missing buckets / source types that the scope clearly needs are flagged (e.g. broad survey with only one paper)
- [ ] **Full-text Markdown availability**: for each paper/web material, check `markdown_status` in the index. If `"converted"` → full-text available for ANALYZE. If `"failed"` or missing → warn the user that ANALYZE will run in **degraded (abstract-only) mode** for that material. If all materials failed conversion, recommend re-running `collect` or manually converting before proceeding.
- [ ] **User consulted**: user was shown the diversity report and asked whether to collect more source types or proceed

**Diversity report (show to user):**

```
Source Type Inventory:
  papers/    : N items  ✓/⚠/✗
  web/       : N items  ✓/⚠/✗
  github/    : N items  ✓/⚠/✗
  datasets/  : N items  ✓/⚠/✗
  models/    : N items  ✓/⚠/✗
Sub-question coverage: Q1 ✓  Q2 ⚠  Q3 ✗  Q4 ✓
Suggested missing types: [list relevant to topic]
```

**Outcomes:**

| Status | Action |
|-------|--------|
| **pass** | Unlock `analyze` in tree-state; recommend `analyze` |
| **warn** | Show gaps, suggest specific source types to collect; user decides: collect more or proceed |
| **fail** | Do not unlock analyze; recommend specific collect actions |

**Failure examples:**
- Only web research syntheses, no primary papers → suggest arXiv collection
- Only papers, no code → suggest GitHub repos for key methods
- Missing entire sub-question area → suggest targeted search
- All materials failed Markdown conversion → suggest re-running collect

A 1-paper deep dive passes with an explicit "narrow corpus" note; a broad survey with one paper fails and asks the user to collect more. Quick-pass skips the pause but still records the check.

Write `.omr/quality-gates/gate-m.json`:

```json
{
  "gate": "M",
  "run_at": "ISO-8601",
  "status": "pass|warn|fail",
  "scenario_note": "e.g. 6 web syntheses + 0 papers — broad but lacks primary sources",
  "checks": [
    {
      "id": "minimum_count",
      "status": "pass|warn|fail",
      "details": "N materials collected"
    },
    {
      "id": "source_diversity",
      "status": "pass|warn|fail",
      "details": "buckets populated: papers=0, web=6, github=0, datasets=0"
    },
    {
      "id": "topic_coverage",
      "status": "pass|warn|fail",
      "details": "sub-questions covered: Q1,Q2,Q3 — Q4 missing"
    },
    {
      "id": "recency",
      "status": "pass|warn|fail",
      "details": "latest source 2025-08; oldest 2018"
    },
    {
      "id": "obvious_gaps",
      "status": "pass|warn|fail",
      "details": "no primary papers collected; github repos absent"
    },
    {
      "id": "full_text_availability",
      "status": "pass|warn|fail",
      "details": "5/6 converted to Markdown; 1 failed (P-003)"
    }
  ],
  "diversity": {
    "papers": 0,
    "web": 6,
    "github": 0,
    "datasets": 0,
    "models": 0
  },
  "suggested_collects": [
    "arxiv: DreamCoder (Ellis et al. 2020) — primary source for program induction",
    "github: salesforce/CodeGen — code generation model repo"
  ]
}
```

**Semi-automated (default):** pause for user decision after showing the diversity report. **Quick-pass:** record JSON, unlock analyze, no pause.

---

## Gate L — Iterate or Advance (Loop only)

Present only when Loop is active or `loop-state.active == true`. Agent updates `.omr/loop-state.json` directly.

**Checks:**
- [ ] Focus question still productive
- [ ] New material / tighter question available for next cycle
- [ ] Confidence / coverage improved since last iteration
- [ ] Ready to exit loop into ANALYZE finish / SYNTH

**Outcomes:** Iterate | Advance | Stop/park

Gate L asks “keep digging?”; Gate A asks “good enough to write the report?”

---

## Gate A — Within ANALYZE

Position: after judgment (+ mandatory THINK in Evidence-Deep), before unlocking SYNTH.

**Checks (interpret for this question — not universal quotas):**
- [ ] Evidence coverage adequate **for the stated scope**
- [ ] Research question clear
- [ ] Scope defined
- [ ] Judgment confidence reasonable and explained
- [ ] Open gaps listed (not hidden)
- [ ] **Three separate artifacts exist**: `brief-*.md`, `evidence-*.md`, `judgment-*.md` (not a single combined file)
- [ ] **THINK pass recorded** (Evidence-Deep only): at least one THINK pass in judgment's THINK ledger. If pattern is Evidence-Deep and no THINK pass exists, Gate A **fails** with `checks: [{id: "think_pass", status: "fail"}]`.
- [ ] **Gate M was recorded**: `gate-m.json` exists under `.omr/quality-gates/`. If not, record it retroactively.

**THINK ledger validation (v1.4 — machine-checkable):**

Gate A must verify the THINK ledger by checking for a literal table in `judgment-*.md` matching this template:

```markdown
## THINK Ledger

| Pass | Method | Date | Outcome |
|------|--------|------|---------|
| 1 | source-triangulation | 2026-08-19 | refined |
```

Validation rules:
- The heading `## THINK Ledger` (or `## THINK Passes Applied`) must exist in `judgment-*.md`
- At least one data row must be present (header-only = fail)
- Each row must have 4 non-empty cells: pass number, method name, date, outcome stamp
- Outcome stamp must be one of: `hardened`, `refined`, `unchanged`, `killed`
- If any rule fails → Gate A fails with `checks: [{id: "think_pass", status: "fail", details: "..."}]`

**Failure:** collect more or `think`; do not unlock SYNTH.

On pass: set `synth` ready in `.omr/tree-state.json`, move `analyze` to `completed`.

---

## QA1 — Post-Analysis Quality (LLM)

Position: after judgment, typically with Gate A. Op: `qa qa1`.

| Check | Guidance (adapt to scenario) |
|-------|------------------------------|
| `coverage` | Enough sources for the claim strength you will make; deep dive on few papers can pass with explicit narrow-scope note; broad survey needs wider coverage |
| `evidence-grade` | Major claim clusters have appropriately strong backing; do not require a fixed count of “proven” |
| `gap-detection` | Open gaps present with severity |
| `contradiction` | Conflicts handled or “None detected” stated |
| `traceability` | Findings link to material IDs in private plans/indexes |
| `full-text-usage` | Verify that ANALYZE read the full-text Markdown (`materials/<bucket>/<ID>.md`) for each material where it exists. Any material analyzed abstract-only (conversion failed or `.md` missing) must be explicitly flagged in the evidence map's traceability notes with reduced confidence. If a material has a converted `.md` but ANALYZE only used the abstract, this is a **fail** — re-run the materials scan. |

Write `.omr/quality-gates/QA1-evidence-analysis.json` with rationale per check.

---

## Gate T — Collect-Decision (after THINK)

Position: after a THINK pass (and after a Gate A failure branch), before re-running Gate A or proceeding.

**Checks:**
- [ ] THINK revelations / collect-targets collected from the playbook's Output contract
- [ ] Determine which surfaced gaps are **load-bearing** for the report vs ignorable
- [ ] If load-bearing gaps exist → ask the user to `collect` more (name the missing source type) **or** explicitly accept proceeding with the gaps documented

**Outcomes:** **collect more** → COLLECT (then re-ANALYZE) | **proceed** → re-run Gate A / continue to SYNTH.

This is the explicit "THINK revealed we need more materials — collect?" decision. A pass that surfaces no load-bearing gaps records `proceed`; one that does, but the user chooses to document-and-continue, records `proceed` with the gaps noted.

---

## Gate B — Before finishing DECIDE (optional)

**Checks:**
- [ ] ≥3 alternatives documented (or document why fewer fit this decision type)
- [ ] Risks stated
- [ ] Evidence refs valid
- [ ] Selection rationale clear

---

## Gate P — Synthesis Preferences (before SYNTH)

Position: after Gate A unlocks SYNTH; before SYNTH Phase A (outline).

**Pre-check (v1.3+):** Verify that `gate-a.json` exists under `.omr/quality-gates/` and has `status: "pass"`. If Gate A was not run, **do not proceed to Gate P** — route back to ANALYZE + THINK + Gate A first. Show `[PHASE-GUARD]` notice if missing.

**Checks (confirm or adjust — record once per report, then keep stable):**
- [ ] Mode: `survey` / `report` / `manuscript` / `brief` (pattern default or user choice)
- [ ] Language: single BCP-47 tag (per `LANGUAGE.md` resolution order)
- [ ] Format: `docx` / `pdf`
- [ ] Audience + intended length/depth
- [ ] Citation style: author–date vs numbered (consistent throughout)
- [ ] Wiki yes/no (if not already specified)

**Outcomes:** **confirm** → SYNTH outline | **adjust** → re-collect preferences.

Consolidates the previously scattered "synth mode if ambiguous" ask and the `--language/--format/--mode` flags into one checkpoint. Quick-pass uses defaults (pattern mode, auto-detected language, `docx`) and records them.

---

## Document Lenses (before Gate D)

Prefer **chapter-scoped** lenses during the long-report loop; one light global pass before export.

| Lens | Method |
|------|--------|
| **Structure** | Cuts, merges, moves — does shape serve a deep report? |
| **Prose** | Clarity, tone, plain explanations, natural evidence-strength phrasing |
| **Adversarial** | Forced missing-angle findings; empty list not allowed |

Process: announce → findings table → user accept/reject → apply → continue.

---

## Gate D — Before Publication

**Pre-check (v1.4):** Verify that `gate-p.json` exists under `.omr/quality-gates/`. If Gate P was not run, **do not proceed to Gate D** — route back to Gate P first. Show `[PHASE-GUARD]` notice if missing.

**Checks:**
- [ ] Claims privately traceable to judgment / evidence-map
- [ ] Public claims use conventional citations only
- [ ] Evidence strength stated naturally (no internal grade labels)
- [ ] No over-claiming
- [ ] Gaps and limitations present
- [ ] Cross-references valid
- [ ] Self-contained for a reader without working files
- [ ] No workflow terms, gate names, internal IDs, or private paths
- [ ] Language consistent (single primary BCP-47 tag)
- [ ] All planned chapters complete in `.omr/report-state.json`
- [ ] Final DOCX/PDF rendered (`export_report.py`) and visually inspected
- [ ] **Incremental writing compliance (v1.4)**:
  - `docs/<mode>/chapters/` directory exists with ≥1 `.md` file (unless brief mode < 3K words)
  - `.omr/report-state.json` exists with `chapters[]` array
  - `docs/<mode>/_outline.md` exists
  - No single chapter file > 5,000 words (warn)
  - Report is not a single un-split `.md` file (fail, unless brief mode exception)
- [ ] **Publication-safety lint passed (v1.4)**: `scripts/report_lint.py` run on all chapter files; no violations (or violations explicitly accepted in `scenario_note`)

---

## QA2 — Pre-Export (LLM)

Op: `qa qa2`. Evaluate chapters under `docs/<mode>/chapters/` (ignore `_*.md` working files).

| Check | Guidance |
|-------|----------|
| `structure` | Outline chapters exist and match report-state; section set fits **this** mode/topic |
| `citations` | Reader-facing cites resolve to complete bibliography entries |
| `coherence` | Order sensible; no orphan stubs; takeaways consistent with continuity |
| `publication-safety` | No internal IDs, workflow/gate jargon (`OMR`, `THINK mode`, `Gate A`), grade labels, or private paths. Product attribution (`Generated by oh-my-research`) is allowed chrome. |
| `self-contained` | Definitions, context, findings, limitations, references stand alone |
| `language` | Consistent language; no mixed boilerplate |
| `rendering` | After export: file exists, opens, typography acceptable |

Write `.omr/quality-gates/QA2-pre-export.json`.

Mechanical backup: `export_report.py` refuses unsafe strings at render time — still fix in prose.

---

## Failure → Options

1. Fix the artifact
2. `think` with a named method
3. `collect` more materials
4. `reconcile` if contradiction cascade
5. Switch pattern or narrow scope (document in `scenario_note`)

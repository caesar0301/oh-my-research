# Quality Gates (Report-First)

Gates are **LLM-evaluated**. The agent reads artifacts, applies the checklists below with scenario judgment, writes results under `.omr/quality-gates/`, and asks the user to confirm (unless quick-pass). See also `LLM-STATE.md`.

## Overview

| Gate | Position | Purpose | Required artifacts |
|------|----------|---------|-------------------|
| **M** | After COLLECT, before ANALYZE | Enough materials to start analysis? | materials + index |
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

## Gate Chain Enforcement (v1.3+)

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

## Gate M — Materials Sufficiency (before ANALYZE)

Position: after COLLECT has ≥1 usable source and `analyze` is marked ready; before ANALYZE's deep pipeline begins.

**Checks (interpret for the intended scope — not a fixed quota):**
- [ ] Material set matches the intended scope (narrow single-paper deep dive vs broad survey)
- [ ] At least one primary source, or an explicit plan to analyze a deliberately small corpus
- [ ] Missing buckets / source types that the scope clearly needs are flagged (e.g. broad survey with only one paper)

**Outcomes:** **proceed** → ANALYZE | **collect more** → return to COLLECT.

A 1-paper deep dive passes with an explicit "narrow corpus" note; a broad survey with one paper fails and asks the user to collect more. Quick-pass skips the pause but still records the check.

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

# Quality Gates (Report-First)

Gates are **LLM-evaluated**. The agent reads artifacts, applies the checklists below with scenario judgment, writes results under `.omr/quality-gates/`, and asks the user to confirm (unless quick-pass). See also `LLM-STATE.md`.

## Overview

| Gate | Position | Purpose | Required artifacts |
|------|----------|---------|-------------------|
| **L** | IDEA / ANALYZE when Loop active | Iterate deeper or advance? | `.omr/loop-state.json` |
| **A** | After ANALYZE judgment, before unlock SYNTH | Evidence sufficient for report? | brief, evidence-map, judgment |
| **QA1** | After judgment (auto or `qa qa1`) | Coverage, gaps, traceability | papers-index, evidence, judgment |
| **B** | Only if DECIDE runs | Stance sound? | decision draft (≥3 alts, risks, refs) |
| **Lenses** | Before Gate D on SYNTH draft | Structure / Prose / Adversarial | `docs/<mode>/chapters/` |
| **D** | Before publishing SYNTH | Traceable, no over-claiming? | judgment (+ optional decision) |
| **QA2** | Pre-export (`qa qa2`) | Structure, citations, coherence, safety | chapters + deliverable |

**Removed:** Gate C and experiment-design checks. **No quality-gate Python runner** — judgment is agent-side.

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

Position: after judgment (+ optional THINK), before unlocking SYNTH.

**Checks (interpret for this question — not universal quotas):**
- [ ] Evidence coverage adequate **for the stated scope**
- [ ] Research question clear
- [ ] Scope defined
- [ ] Judgment confidence reasonable and explained
- [ ] Open gaps listed (not hidden)

**Failure:** collect more or `think`; do not unlock SYNTH.

On pass: set `synth` ready in `.omr/tree-state.json`.

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

## Gate B — Before finishing DECIDE (optional)

**Checks:**
- [ ] ≥3 alternatives documented (or document why fewer fit this decision type)
- [ ] Risks stated
- [ ] Evidence refs valid
- [ ] Selection rationale clear

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

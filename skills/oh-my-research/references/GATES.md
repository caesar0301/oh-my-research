# Quality Gates (Report-First)

## Overview

| Gate | Position | Purpose | Required artifacts |
|------|----------|---------|-------------------|
| **L** | IDEA / ANALYZE when Loop active | Iterate deeper or advance? | `.omr/loop-state.json` |
| **A** | After ANALYZE judgment, before unlock SYNTH | Evidence sufficient for report? | brief, evidence-map, judgment |
| **QA1** | After judgment (auto or `qa qa1`) | Coverage, gaps, traceability metrics | papers-index, evidence, judgment |
| **B** | Only if DECIDE runs | Stance sound? | decision draft (≥3 alts, risks, refs) |
| **Lenses** | Before Gate D on SYNTH draft | Structure / Prose / Adversarial | synthesis draft under `docs/<mode>/` |
| **D** | Before publishing SYNTH | Traceable, no over-claiming? | judgment (+ optional decision) |
| **QA2** | Pre-export (`qa qa2`) | Structure, citations, coherence | synthesis files |

**Removed:** Gate C and all experiment-design checks.

## Enforcement Modes

| Mode | Behavior |
|------|----------|
| **Semi-automated** (default) | User confirms at each gate |
| **Quick-pass / no confirmations** | Gates auto-pass after checks run (still record results) |
| **Fully-automated** | Same as quick-pass; for agent-driven runs |

Record passes under `.omr/quality-gates/`.

---

## Gate L — Iterate or Advance (Loop only)

Present only when Loop pattern is active or `loop-state.active == true`.

**Checks:**
- [ ] Focus question still productive
- [ ] New material / tighter question available for next cycle
- [ ] Confidence / coverage improved since last iteration
- [ ] Ready to exit loop into ANALYZE finish / SYNTH

**Outcomes:** Iterate | Advance | Stop/park

Helper: `scripts/loop_state.py`

Gate L asks “keep digging?”; Gate A asks “good enough to write the report?”

---

## Gate A — Within ANALYZE

Position: after judgment (+ optional THINK), before unlocking SYNTH / writing optional plan.

**Checks:**
- [ ] Evidence coverage adequate for the research question
- [ ] Research question clear
- [ ] Scope defined
- [ ] Judgment confidence reasonable
- [ ] Open gaps listed (not hidden)

**Failure:** “Evidence insufficient. Add materials via `collect` or deepen with `think` (e.g. Source Triangulation / First Principles).” Re-run judgment phases before unlocking SYNTH.

---

## QA1 — Post-Analysis Quality

Position: after judgment, typically before or with Gate A.

| Check | Criteria |
|-------|----------|
| `coverage` | Prefer ≥3 primary sources on core themes; total materials ≥5 for deep survey (scale with topic) |
| `evidence-grade` | At least some `proven` or multiple `suggests` per major claim cluster |
| `gap-detection` | Open gaps section present with severity |
| `contradiction` | Conflicts flagged or “None detected” stated |
| `traceability` | Every finding links to material ID present in indexes |

Write: `.omr/quality-gates/QA1-evidence-analysis.json`

Script: `scripts/quality_gate.py qa1`

---

## Gate B — Before finishing DECIDE (optional path only)

**Checks:**
- [ ] ≥3 alternatives documented
- [ ] Risks stated
- [ ] Evidence refs valid
- [ ] Selection rationale clear

**Failure:** Complete alternatives / risks / refs before marking decision done.

---

## Document Lenses (before Gate D)

BMAD-inspired multi-lens review on synthesis drafts. Content ideas are not “corrected away” by Structure/Prose; Adversarial finds missing angles.

| Lens | Method |
|------|--------|
| **Structure** | Propose cuts, merges, moves — does shape serve a deep report? |
| **Prose** | Clarity, flow, professional tone, plain-language explanations, natural evidence-strength phrasing |
| **Adversarial** | Forced missing-angle findings (≥ several concrete gaps); empty list not allowed |

Process:
1. Announce lenses
2. Produce findings table (lens, location, trigger, consequence)
3. User accept/reject row by row
4. Apply accepted edits
5. Proceed to QA2 / Gate D

---

## Gate D — Before Publication

**Checks:**
- [ ] Claims privately traceable to judgment / evidence-map
- [ ] Public claims use conventional author–date or numbered citations
- [ ] Evidence strength is stated naturally, without internal grade labels
- [ ] No over-claiming
- [ ] Gaps and limitations section present
- [ ] Cross-references valid
- [ ] Report is self-contained for a reader without access to working artifacts
- [ ] No OMR/workflow terminology, gate names, internal IDs, or artifact paths remain
- [ ] Language is idiomatic professional English or Simplified Chinese
- [ ] Final DOCX/PDF has been rendered and visually inspected

**Failure:** Fix links, boundaries, or over-claims; re-run lenses if structural.

---

## QA2 — Pre-Export

| Check | Criteria |
|-------|----------|
| `structure` | Required sections for mode (survey/report/…) present |
| `citations` | Reader-facing citations resolve to complete bibliography entries |
| `coherence` | No orphan chapters; TOC matches files |
| `publication-safety` | No internal IDs, OMR terms, gate names, grade labels, or private paths |
| `self-contained` | Definitions, context, method, findings, limitations, and references stand alone |
| `language` | Consistent `en` or `zh-CN`; no accidental mixed-language boilerplate |
| `rendering` | DOCX/PDF opens cleanly; headings, tables, page breaks, fonts, and page numbers are correct |

Write: `.omr/quality-gates/QA2-pre-export.json`

Script: `scripts/quality_gate.py qa2`

---

## Gate Metadata Example

```yaml
gates_passed:
  - gate: gate_a
    passed_at: 2026-08-18T10:00:00Z
    reviewer: user
    checks:
      - "Evidence coverage: ✓"
      - "Question clear: ✓"
```

## Failure → Options

1. Fix the artifact
2. `think` with a named method
3. `collect` more materials
4. `reconcile` if contradiction cascade
5. Switch pattern (e.g. Rapid for time-box)

# ANALYZE Mode — Deep Analysis

Transform collected materials into a research brief, evidence map, judgment summary, and optional research plan. **Centerpiece** of Oh-My-Research. Enforces evidence boundaries and a THINK depth checkpoint before Gate A unlocks SYNTH.

## Trigger

```
analyze
```

Also: “analyze these papers”, “map evidence”, “now what” after collect.

**Requires:** ≥1 material under `materials/` and `docs/index/papers-index.json` (or other indexes with entries).

### Pre-flight: Phase-Guard Check

Before starting, read `.omr/tree-state.json`. If `analyze` is not in `ready` or `unlocked`, check if prerequisites are met (materials + index). If they are, update tree-state to mark `analyze` as `ready`. If materials are missing, route to COLLECT instead.

## Mandatory Output Artifacts (Non-negotiable)

ANALYZE **must** produce all three required artifacts as **separate files**. Using a single combined file (e.g. `deep-analysis.md`) as a substitute is **not acceptable** — downstream stages (THINK, Gate A, SYNTH) depend on reading specific artifact files by name pattern.

| Artifact | File pattern | Required sections |
|---|---|---|
| **Research brief** | `docs/plans/brief-{id}.md` | Question, scope, material inventory, themes, out-of-scope |
| **Evidence map** | `docs/plans/evidence-{id}.md` | Primary evidence, supporting evidence, contradictions, gaps (H/M/L), traceability |
| **Judgment** | `docs/plans/judgment-{id}.md` | Main conclusion (boundary-tagged), confidence (H/M/L) + rationale, contradictions, open questions, THINK ledger |

If the agent produces a single combined file instead of three separate files, Gate A **will fail** with `checks: [{id: "artifact_separation", status: "fail"}]`.

## Pipeline

### 0. Gate M — enough materials?

Before the deep scan, run **Gate M** (see `GATES.md`): is the material set sufficient for the intended scope? If a broad survey has only one paper (or the scope clearly needs a missing source type), pause and ask the user to `collect` more. A deliberate narrow corpus (e.g. single-paper deep dive) passes with a "narrow corpus" note.

### 1. Scope and research questions

1. Scan indexes (`papers-index`, blogs/web, github).
2. Derive candidate research question from themes (keyword clustering).
3. Confirm with user: Accept / Edit / Provide own.
4. Optional: offer THINK `reframe-the-question` or First Principles on the question.

### 2. Materials scan → graded findings

For each material:
- **Read the full-text Markdown file** (`materials/<bucket>/<ID>.md`) — this is the primary source for analysis. The full paper body (introduction, methods, results, discussion, tables, figures captions) must be read, not just the abstract.
- If `markdown_path` exists in the index entry and the `.md` file is present → **read it in full**. For long papers, read in sections (offset/limit pagination) but cover the entire document.
- If `markdown_status` is `"failed"` or the `.md` file is missing → **degraded mode**: fall back to abstract/metadata only, but record this explicitly in the evidence map as a traceability note (`[P-001: abstract-only — full-text conversion failed]`) and flag the finding's confidence as reduced.
- Extract contributions, methods, limitations from the **full paper body**, not the abstract alone.
- Map author language → evidence grade:

| Author language | Grade |
|-----------------|-------|
| prove / validate (strong) | `proven` |
| demonstrate / show / suggest | `suggests` |
| hypothesize / propose / may | `inferred` (or speculative — exclude as anchor) |

**Non-negotiable:** never claim proves when source only suggests.

Every finding cites material ID (`[P-001]`, `[W-002]`, …).

### 3. Evidence map → `docs/plans/evidence-{id}.md`

Sections:
- Primary evidence
- Supporting evidence
- Contradictions
- Open gaps (with severity: High / Medium / Low)
- Traceability notes (including **full-text vs abstract-only** status per material — any material analyzed in degraded mode must be flagged here)

### 4. Research brief → `docs/plans/brief-{id}.md`

Question, scope, material inventory, themes, out-of-scope.

### 5. Judgment → `docs/plans/judgment-{id}.md`

- Main conclusion (boundary-tagged)
- Confidence (high / medium / low) + rationale
- Contradictions handling
- Open questions
- Implications for the report narrative
- **THINK Ledger** section (see template below) — must exist even before first THINK pass (starts empty, filled after each pass)

**THINK Ledger template (v1.4 — mandatory section in judgment):**

```markdown
## THINK Ledger

| Pass | Method | Date | Outcome |
|------|--------|------|---------|
```

The ledger starts as an empty table (header only). After each THINK pass, add a row. Gate A validates this table has ≥1 data row in Evidence-Deep pattern. See `GATES.md` § Gate A — THINK ledger validation.

### 6. THINK checkpoint (Evidence-Deep default — mandatory)

**In Evidence-Deep pattern, THINK is MANDATORY after judgment — not optional.** The THINK checkpoint must run at least one pass before Gate A can pass. This prevents the common failure mode where ANALYZE produces a judgment and immediately proceeds to SYNTH without any depth elicitation.

**Trigger conditions (any one suffices):**
- Pattern is Evidence-Deep (default) — **always offer THINK**
- Confidence is low/medium
- High-severity gaps exist

**Procedure:**
1. Present a **method selection menu** with 5 best-fit methods (see `THINK/think.md` § Behavior). Recommended defaults for judgment: **First Principles**, **Source Triangulation**, **Steelmanning**, **Pre-mortem**, **Thesis Defense**.
2. User selects a method (or agent picks the best-fit if quick-pass).
3. Load the method's playbook from `THINK/methods/<slug>.md`.
4. Apply its procedure: trigger questions → analysis → revelations (≥1 required, never default-agree).
5. Produce proposed edits + outcome stamp (`hardened`/`refined`/`unchanged`/`killed`).
6. Ask user: **y / n / other** — never mutate without yes.
7. Record the pass in the judgment's THINK ledger — append a row to the `## THINK Ledger` table (see template in §5). The row must have: pass number, method name, date (ISO-8601), outcome stamp (`hardened`/`refined`/`unchanged`/`killed`). Gate A will validate this table exists and has ≥1 row.
8. Re-save judgment / evidence-map if edits accepted.

**Gate A cannot pass without at least one THINK pass recorded in the judgment's THINK ledger.** If the user explicitly skips THINK (quick-pass or "just proceed"), record `scenario_note: "THINK skipped by user override"` in `gate-a.json` — but the agent must still ask, not silently skip.

### 6a. Gate T — collect more?

After each THINK pass, run **Gate T** (see `GATES.md`): did the pass surface load-bearing material gaps (e.g. a missing source type from Source Triangulation, an unreplicated anchor from Pre-mortem)? If so, ask the user to `collect` the missing type, or explicitly accept proceeding with the gap documented. Collecting more loops back to COLLECT → re-ANALYZE.

### 7. Gate L (Loop only)

If loop active → iterate vs advance per `GATES.md`.

### 8. Gate A / QA1

Run checks in `GATES.md`. On pass → unlock SYNTH in tree-state. On fail → collect more or THINK again.

### 9. Optional plan → `docs/plans/plan-{id}.md`

Priorities for further collection or report chapter outline — **not** a coding plan.

## Outputs

| File | Required |
|------|----------|
| `brief-{id}.md` | **yes** (separate file, not combined) |
| `evidence-{id}.md` | **yes** (separate file, not combined) |
| `judgment-{id}.md` | **yes** (separate file, with THINK ledger) |
| `plan-{id}.md` | optional |

Default id: `R-001`.

### Post-completion: Update tree-state

After ANALYZE completes (Gate A passed), **update `.omr/tree-state.json`**:
- Move `analyze` from `ready` to `completed`
- Move `synth` from `locked` to `ready` (Gate A pass unlocks SYNTH)
- Keep `think` in `unlocked` (always available)
- Add `notes` field with Gate A result summary

```json
{
  "unlocked": ["init", "collect", "idea", "think"],
  "ready": ["synth", "decide"],
  "locked": ["reconcile"],
  "completed": ["init", "collect", "analyze"],
  "notes": "Gate A passed. THINK: 1 pass (first-principles, hardened). Ready for synth."
}
```

## Chat reply

Short summary only: paths written, confidence, gap count, Gate A status, recommended next (`think` / `synth` / `collect`).

## Templates

`assets/plans/brief-template.md`, `evidence-map-template.md`, `judgment-template.md`, `plan-template.md`.

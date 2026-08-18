# ANALYZE Mode — Deep Analysis

Transform collected materials into a research brief, evidence map, judgment summary, and optional research plan. **Centerpiece** of Oh-My-Research. Enforces evidence boundaries and a THINK depth checkpoint before Gate A unlocks SYNTH.

## Trigger

```
analyze
```

Also: “analyze these papers”, “map evidence”, “now what” after collect.

**Requires:** ≥1 material under `materials/` and `docs/index/papers-index.json` (or other indexes with entries).

## Pipeline

### 1. Scope and research questions

1. Scan indexes (`papers-index`, blogs/web, github).
2. Derive candidate research question from themes (keyword clustering).
3. Confirm with user: Accept / Edit / Provide own.
4. Optional: offer THINK `reframe-the-question` or First Principles on the question.

### 2. Materials scan → graded findings

For each material:
- Extract contributions, methods, limitations (from abstract/metadata; PDF text when needed)
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
- Traceability notes

### 4. Research brief → `docs/plans/brief-{id}.md`

Question, scope, material inventory, themes, out-of-scope.

### 5. Judgment → `docs/plans/judgment-{id}.md`

- Main conclusion (boundary-tagged)
- Confidence (high / medium / low) + rationale
- Contradictions handling
- Open questions
- Implications for the report narrative

### 6. THINK checkpoint (Evidence-Deep default)

If confidence is low/medium **or** High gaps exist **or** pattern is Evidence-Deep:
- Offer 1–2 methods (recommend **First Principles** or **Source Triangulation**)
- Follow `THINK/think.md` (confirm before edit)
- Re-save judgment / evidence-map if accepted

### 7. Gate L (Loop only)

If loop active → iterate vs advance per `GATES.md`.

### 8. Gate A / QA1

Run checks in `GATES.md`. On pass → unlock SYNTH in tree-state. On fail → collect more or THINK again.

### 9. Optional plan → `docs/plans/plan-{id}.md`

Priorities for further collection or report chapter outline — **not** a coding plan.

## Outputs

| File | Required |
|------|----------|
| `brief-{id}.md` | yes |
| `evidence-{id}.md` | yes |
| `judgment-{id}.md` | yes |
| `plan-{id}.md` | optional |

Default id: `R-001`.

## Chat reply

Short summary only: paths written, confidence, gap count, Gate A status, recommended next (`think` / `synth` / `collect`).

## Templates

`assets/plans/brief-template.md`, `evidence-map-template.md`, `judgment-template.md`, `plan-template.md`.

# THINK Mode — Research Elicitation

Shared refinement checkpoint adapted from BMAD advanced elicitation. Applies **named thinking paradigms** to research artifacts (evidence-map, judgment, report chapters) — **never to code**.

## Trigger

```
think
think first-principles
think socratic
think source-triangulation
deepen judgment
rethink the evidence map
```

Intent keywords: `first principles`, `socratic`, `pre-mortem`, `red team`, `steelman`, `deepen`, `rethink`, `elicit`, `think`.

## Behavior

1. **Target** = most recent research artifact in the session, or path the user names (`docs/plans/judgment-R-001.md`, a synth chapter, etc.).
2. If user named a method → use it. Else offer **5 best-fit** methods from `assets/think/methods.csv` (see `methods.md` for when-to-use). Prefer research-core methods for judgment/evidence; reshuffle excludes already offered.
3. Apply method using its `output_pattern` as a flexible flow. Scale depth to target size.
4. Show: what the method revealed + proposed edits (diff-style summary).
5. Ask **y / n / other** — **never mutate without yes**. On no, drop proposal. Other text = revise instruction.
6. Compound passes on the enhanced version until user says **proceed**.
7. Return to ANALYZE or SYNTH (caller resumes).

## Recommended defaults by artifact

| Artifact | First offer |
|----------|-------------|
| Research question / brief | Reframe the Question, First Principles, Abstraction Laddering |
| Evidence map | Source Triangulation, Assumption Audit, Literature Review Personas |
| Judgment | First Principles, Thesis Defense, Steelmanning, Pre-mortem |
| Synth chapter | Critique and Refine, Adversarial (via SYNTH lenses), Inversion, Feynman |

## Auto-offer checkpoints

- After ANALYZE judgment draft if confidence low or gaps high → offer First Principles **or** Source Triangulation
- After SYNTH chapter draft before document lenses → offer Critique and Refine (optional; lenses still run)

## Hard rules

- Preserve evidence grades; THINK may **downgrade** over-claims, never silently upgrade `suggests` → `proven`
- Keep citation IDs intact; if a claim cannot be cited, mark as gap or inferred with boundary
- Do not invent sources

## Catalog

Full method list and patterns: `methods.md` + `assets/think/methods.csv`.

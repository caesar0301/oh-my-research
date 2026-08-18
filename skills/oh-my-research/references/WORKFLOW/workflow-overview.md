# Workflow Overview — Evidence-Deep

## Objective

Run the default report-first lifecycle with clear phase visibility:

```
[INIT] → [COLLECT] → [ANALYZE] (+ [THINK]) → [SYNTH] → [FINISHED]
```

## Phase visibility

Always show current phase in status lines, e.g. `[ANALYZE] Pattern: Evidence-Deep`.

## End-to-end path

### 1. INIT

```
init "agent memory mechanisms"
```

Creates `AGENTS.md`, `.omr/tree-state.json`, `.omr/pattern.json` = Evidence-Deep.

### 2. COLLECT

```
collect https://arxiv.org/abs/2401.xxxxx
collect "lifecycle formation evolution survey"
```

Materials land under `materials/`; indexes under `docs/index/`. Tree: `analyze` becomes ready.

### 3. ANALYZE

```
analyze
```

Produces brief, evidence-map, judgment (id `R-001`).  
Depth checkpoint: offer `think first-principles` or Source Triangulation when confidence/gaps warrant.

```
think first-principles
```

User confirms edits → refresh judgment.

Present **Gate A / QA1**. On pass → unlock SYNTH.

### 4. SYNTH

```
synth --mode survey
```

Draft `docs/survey/…` → document lenses (Structure, Prose, Adversarial) → QA2 → **Gate D**.  
On pass: optional wiki. Chat: summary only.

### 5. FINISHED

```
version tag v1.0-survey
```

Optional: more `collect` + `reconcile` if new contradictory papers arrive.

## workflow op

```
workflow
workflow --pattern Evidence-Deep
workflow --pattern Rapid
```

Runs recommended next steps along the active graph, pausing at gates unless user requested quick-pass / no confirmations.

## Alternate patterns (short)

| Pattern | Path |
|---------|------|
| Evidence-First | collect → analyze → synth (THINK optional) |
| Idea-First | idea → collect → analyze ⟲ think → synth (brief) |
| Stance-First | decide → collect → analyze → synth (report) |
| Loop | Gate L cycles then synth |
| Rapid | collect → analyze → synth, gates off |

## When to ask the user

- Research question wording (ANALYZE)
- Synth mode if ambiguous (survey vs report)
- Gate confirmations (unless quick-pass)
- THINK method choice when menu shown
- Wiki yes/no if not specified

## Phase files

- This file — overview + Evidence-Deep e2e
- `workflow-phases.md` — phase checklist detail

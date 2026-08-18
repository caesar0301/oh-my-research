# Workflow Phases — Checklist

## [INIT]

- [ ] Topic confirmed
- [ ] `AGENTS.md` written
- [ ] `.omr/tree-state.json` + `pattern.json` (Evidence-Deep default)
- [ ] User shown `collect` next step

## [COLLECT]

- [ ] Inputs routed to handlers
- [ ] Files under `materials/`
- [ ] Indexes updated with stable IDs
- [ ] Failures logged
- [ ] `analyze` marked ready when ≥1 usable source

## [ANALYZE]

- [ ] Question confirmed
- [ ] Findings graded (`proven` / `suggests` / `inferred`)
- [ ] `brief-*`, `evidence-*`, `judgment-*` written
- [ ] THINK offered/run when Evidence-Deep or low confidence
- [ ] Gate L if Loop
- [ ] QA1 + Gate A passed
- [ ] Optional `plan-*` for further collection / chapter outline

## [THINK] (side-cycle)

- [ ] Target artifact identified
- [ ] Method selected (named or menu of 5)
- [ ] Revelations + proposals shown
- [ ] User y/n before mutation
- [ ] Return to ANALYZE or SYNTH

## [DECIDE] (optional)

- [ ] ≥3 alternatives
- [ ] Gate B passed
- [ ] Decision file written

## [SYNTH]

- [ ] Mode selected
- [ ] Chapters written to `docs/<mode>/`
- [ ] Citations resolve
- [ ] Gaps/limitations section present
- [ ] Lenses run; accepted edits applied
- [ ] QA2 + Gate D passed
- [ ] Wiki generated or skipped
- [ ] Chat summary only

## [RECONCILE] (as needed)

- [ ] Blast radius identified
- [ ] Archive + updates applied
- [ ] Gates re-checked if judgment/synth changed

## [FINISHED]

- [ ] Version tag recommended
- [ ] Next research questions listed from gaps

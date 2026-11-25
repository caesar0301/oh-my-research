# Oh-My-Research — Complete Reference

> Load when: locating the right reference file (File Index), artifact naming, evidence boundaries, or troubleshooting. Depth: lean.

## Contents

- [File Index](#file-index)
- [Operations Index](#operations-index)
- [Auto-Detection Decision Tree](#auto-detection-decision-tree)
- [Artifact Naming](#artifact-naming)
- [Evidence Boundaries (non-negotiable)](#evidence-boundaries-non-negotiable)
- [Tree State](#tree-state)
- [Template Variables](#template-variables)
- [Troubleshooting](#troubleshooting)

Detailed operation guide for the unified OMR skill.

## File Index

Every loadable doc in the skill, one line each. Grep this file to locate a doc without opening it: `grep -i '<keyword>' references/REFERENCE.md`. Each file's own `> Load when:` line (directly under its H1) is the authoritative load condition; the table below is the scan-friendly catalog.

**Core (always relevant when the topic matches)**

| File | Role | Keywords |
|------|------|----------|
| `references/GATES.md` | All gates, QA checklists, confirmation-enforcement CLI | gate, confirm, pause, chain, M, A, T, P, D, QA1, QA2 |
| `references/GRAPH.md` | Pattern graphs, unlock rules, next-step routing | pattern, evidence-deep, loop, unlock, tree-state |
| `references/LANGUAGE.md` | Timezone/locale → preferred BCP-47 language | language, locale, timezone, bcp-47 |
| `references/LLM-STATE.md` | `.omr/` state JSON schemas (agent-authored) | tree-state, loop-state, report-state, gate-mode, locale, quality-gates |
| `references/REFERENCE.md` | This file — file index, naming, boundaries, troubleshooting | index, naming, evidence boundaries, troubleshooting |
| `scripts/README.md` | Mechanical scripts: flags, defaults, examples | gate_cli, export_report, collect_cli, material_to_markdown, prose_lint, report_lint, version_control |

**Operation modes**

| File | Role | Keywords |
|------|------|----------|
| `references/INIT/init.md` | Bootstrap topic workspace; scan working root for existing topics | init, workspace, agents.md, topic |
| `references/COLLECT/collect.md` | Four-bucket collect, full-text conversion, Gate M | collect, bucket, papers, web, github, search, download, convert |
| `references/COLLECT/agents/bucket-worker.md` | Parallel bucket-worker protocol | parallel, worker, inbox, bucket |
| `references/ANALYZE/analyze.md` | Brief → evidence map → judgment pipeline | analyze, brief, evidence map, judgment, think ledger |
| `references/THINK/think.md` | THINK pass protocol: selection, ledger, stamps | think, method, stamp, hardened, refined, killed |
| `references/THINK/methods.md` | One-line THINK method catalog | method, catalog |
| `references/THINK/methods/README.md` | Playbook index + output-contract anatomy | playbook, revelations, proposed edits, stamp |
| `references/SYNTH/synth.md` | SYNTH entry: modes, quality bar, layouts, chat replies | synth, survey, report, mode, layout |
| `references/SYNTH/long-report.md` | Chapter loop Phases A–F, resume, export | chapter, outline, citation map, continuity, resume, export |
| `references/SYNTH/narrative-coherence.md` | Reader journey, chapter contracts, Narrative Audit | reader journey, argument spine, contract, 起承转合, audit |
| `references/SYNTH/native-expression.md` | Native-expression rules + prose budgets | translationese, metaphor, heading, rhythm, prose_lint |
| `references/IDEA/idea.md` | Speculative notes | idea, brainstorm, hypothesis |
| `references/DECIDE/decide.md` | Stance framing with ≥3 alternatives, Gate B | decide, stance, alternatives, gate b |
| `references/RECONCILE/reconcile.md` | Contradiction blast-radius, archive, rollback | contradiction, archive, rollback |
| `references/VERSION/version.md` | Workspace tagging / backups | tag, history, diff, backup |
| `references/WORKFLOW/workflow-overview.md` | Multi-phase workflow, pattern comparison | workflow, phase, pattern |
| `references/WORKFLOW/workflow-phases.md` | Per-phase checklists | checklist, phase |

**THINK method playbooks** (`references/THINK/methods/` — load only the method being run)

| File | Intent | Depth |
|------|--------|-------|
| `first-principles.md` | Rebuild from fundamental truths | deep |
| `source-triangulation.md` | Require ≥3 independent sources per claim | deep |
| `pre-mortem.md` | Rehearse failure before it happens | deep |
| `steelmanning.md` | Build the strongest counter-case | deep |
| `assumption-audit.md` | Rate and stress-test assumptions | deep |
| `red-team-vs-blue-team.md` | Adversarial pair critique | deep |
| `second-order-thinking.md` | Trace consequence chains | deep |
| `socratic-questioning.md` | Surface hidden assumptions | lean |
| `literature-review-personas.md` | Optimist / skeptic / synthesizer | lean |
| `thesis-defense.md` | Committee stress-tests conclusions | lean |
| `chain-of-thought.md` | Explicit reasoning steps | lean |
| `inversion.md` | Solve the opposite problem | lean |
| `occams-razor.md` | Prefer the simplest explanation | lean |
| `problem-decomposition.md` | Split into sub-problems | lean |
| `abstraction-laddering.md` | Shift abstraction level | lean |
| `comparative-analysis-matrix.md` | Structured comparison table | lean |
| `critique-and-refine.md` | Iterative critique loop | lean |
| `explain-reasoning.md` | Make reasoning explicit | lean |
| `feynman-technique.md` | Explain-it-simply test | lean |
| `reframe-the-question.md` | Reframe the problem statement | lean |

**Assets and patterns** (templates and machine-readable graphs — not agent docs)

| Path | Role |
|------|------|
| `assets/templates/AGENTS.md.template` | Workspace `AGENTS.md` scaffold |
| `assets/templates/idea-note-template.md` | Idea note scaffold |
| `assets/plans/*.md` | brief / evidence / judgment / plan / decision templates |
| `assets/synth/_*.md` | Outline / continuity / narrative-audit working files |
| `patterns/*.json` | Machine-readable pattern graphs (routing + advisory agency) |

---

## Operations Index

| Mode | Ops | Reference |
|------|-----|-----------|
| INIT | `init` | `INIT/init.md` |
| COLLECT | `collect` | `COLLECT/collect.md` |
| ANALYZE | `analyze` | `ANALYZE/analyze.md` |
| THINK | `think [method]` | `THINK/think.md`, `THINK/methods.md`, `THINK/methods/` (playbooks) |
| SYNTH | `synth [--mode] [--format] [--language] [--resume] [--chapter] [--no-wiki]` | `SYNTH/synth.md`, `SYNTH/long-report.md` |
| QA | `qa qa1\|qa2\|all\|state-check` | `GATES.md`, `LLM-STATE.md` |
| IDEA | `idea` | `IDEA/idea.md` |
| DECIDE | `decide` | `DECIDE/decide.md` |
| RECONCILE | `reconcile`, `archive`, `rollback`, `list` | `RECONCILE/reconcile.md` |
| WORKFLOW | `workflow [--phase N] [--pattern P]` | `WORKFLOW/workflow-overview.md` |

Cross-cutting: `GATES.md`, `GRAPH.md`, `LLM-STATE.md`, `LANGUAGE.md`.

---

## Auto-Detection Decision Tree

The full decision tree — intention detection, workspace-state detection, and Phase-Guard routing — lives in `../SKILL.md` as a Mermaid flowchart. Canonical op names (`init`, `collect`, `analyze`, `think`, `synth`, `decide`, `idea`, `reconcile`, `workflow`, `qa`) always win over keyword routing.

**Intent keyword summary** (case-insensitive):

| Signal | Route |
|---------------------------|-------|
| `first principles`, `socratic`, `pre-mortem`, `red team`, `steelman`, `deepen`, `rethink`, `elicit`, `think` | **THINK** on latest artifact |
| `idea`, `brainstorm`, `speculate`, `what if`, `hypothesis` | **IDEA** |
| URL / DOI / arxiv / GitHub / HuggingFace / `search …` / `collect` | **COLLECT** (init-on-demand if needed) |
| `report`, `survey`, `write up`, `synthesize`, `manuscript`, `brief` | **SYNTH** (Phase-Guard checked) |

---

## Artifact Naming

Resolve the **active workspace** first (see `SKILL.md` § Workspace resolution): an explicit `--workspace` path, otherwise `<project-root>/.omr/<topic-slug>/` under the default working root. All paths below are relative to the active workspace root.

| Artifact | Pattern | Location |
|----------|---------|----------|
| Research brief | `brief-{id}.md` | `docs/plans/` |
| Evidence map | `evidence-{id}.md` | `docs/plans/` |
| Judgment | `judgment-{id}.md` | `docs/plans/` |
| Research plan | `plan-{id}.md` | `docs/plans/` |
| Decision (optional) | `decision-DEC-{nnn}.md` | `docs/plans/` |
| Idea note | `YYYY-MM-DD-<slug>.md` | `docs/ideas/` |
| Papers index | `papers-index.json` (+ `.md`) | `docs/index/` |
| Synthesis drafts | chapters + spec under mode dir | `docs/{survey,report,manuscript,brief}/` |
| Deliverable (public) | `<topic>-<mode>-<lang>.<ext>` | `deliverables/` (optional `deliverables/wiki/`) |
| Gate confirmation mode | `gate-mode.json` | `.omr/` (written by `gate_cli.py init`) |
| Gate / QA results | `gate-*.json`, `QA1-*.json`, `QA2-*.json` | `.omr/quality-gates/` (written by `gate_cli.py record`) |
| Material IDs | `P-xxx` papers, `W-xxx` web, `G-xxx` github | indexes |
| Full-text Markdown | `materials/<bucket>/<ID>.md` | papers: `materials/papers/`; also `web`, `github` |
| Paper raw binaries | `materials/papers-raw/<ID>.<ext>` | same stem as the Markdown file |

`{id}` default: `R-001` for first research thread (increment if multiple threads).

**Layout rule:** locations above are destinations for real files under the active workspace. Never create those directories empty — write the file (parent dirs appear as a side effect). INIT only creates `AGENTS.md` + `.omr/*.json`. See `INIT/init.md`.

---

## Evidence Boundaries (non-negotiable)

| Level | Label | Meaning |
|-------|-------|---------|
| **proven** | "Paper X validates / proves…" | Strong experimental or formal validation in source |
| **suggests** | "Paper X suggests / demonstrates…" | Indirect or limited evidence |
| **inferred** | "Based on X, we infer…" | Multi-source synthesis; explicit boundary |
| **speculative** | — | Exclude from evidence map as anchor |

Never claim "proves" when authors only suggest or demonstrate.

---

## Tree State

File: `.omr/tree-state.json`

```json
{
  "unlocked": ["init", "collect", "idea", "think"],
  "ready": ["analyze"],
  "locked": ["synth", "decide", "reconcile"],
  "completed": []
}
```

Update after each op using graph rules in `GRAPH.md` (LLM edits `.omr/tree-state.json` — see `LLM-STATE.md`).

---

## Template Variables

Templates use `{{PLACEHOLDER}}` syntax. Each template file declares its own placeholders inline (e.g. `AGENTS.md.template` needs project/language fields, `judgment-template.md` needs evidence/confidence fields) — read the file you are filling instead of relying on a central list.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Wrong auto-detection | Use explicit op (`analyze`, `synth`, `think first-principles`) |
| Gate A fails | Collect more materials or run THINK (triangulation / first principles) |
| Shallow judgment | `think` with Literature Review Personas or Thesis Defense |
| Over-claiming in draft | Lenses + Gate D; fix evidence boundaries |
| Missing citations | Ensure every claim has `[P-xxx]` / `[W-xxx]` linked in index |
| Stuck after collect | Run `analyze` |

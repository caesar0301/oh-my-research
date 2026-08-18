# Oh-My-Research (OMR)

A unified Agent Skill for **high-quality deep research reports** from collected materials and evidence.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Agent Skills Format](https://img.shields.io/badge/format-Agent%20Skills%201.0-blue)](https://agentskills.io)

## Overview

**Oh-My-Research** is a single orchestrator skill that turns literature and web materials into evidence-bound surveys and reports, with:

- **Intent + workspace-state auto-detection**
- **Graph-guided patterns** (default: Evidence-Deep)
- **Confirmation gates** (A / D / L; optional B)
- **THINK mode** — structured thinking paradigms (first principles, Socratic, triangulation, …)
- **Document lenses** before publish (Structure / Prose / Adversarial)
- **Professional Word/PDF delivery** in English or Simplified Chinese
- **Publication-safe output** with standard citations and no internal workflow terminology

Primary pipeline:

```
COLLECT materials → ANALYZE (deep evidence + THINK) → SYNTH (incremental long report → Word/PDF)
```

Deep reports are written chapter-by-chapter to disk (with a continuity brief and resume support), then assembled into a professional Word or PDF document.

## Installation

### Claude Code Marketplace

```text
/plugin marketplace add <owner>/oh-my-research
/plugin install oh-my-research@oh-my-research
/reload-plugins
```

### npx skills

```bash
npx skills add <owner>/oh-my-research
```

## Available Skill

| Skill | Purpose |
|-------|---------|
| **oh-my-research** | Unified research orchestrator: init, collect, analyze, think, synth, reconcile, version |

## Canonical Operations

| Op | Mode | Output |
|----|------|--------|
| `init` | INIT | `AGENTS.md`, `.omr/tree-state.json` |
| `collect` | COLLECT | `materials/**`, indexes |
| `analyze` | ANALYZE | brief, evidence-map, judgment, plan |
| `think [method]` | THINK | refined artifact |
| `synth [--mode] [--format docx\|pdf] [--language en\|zh-CN]` | SYNTH | Professional, self-contained Word/PDF report |
| `decide` | DECIDE | optional stance (Gate B) |
| `idea` | IDEA | idea note |
| `reconcile` | RECONCILE | repaired state / archive |
| `version …` | VERSION | tags / backups |
| `workflow` | WORKFLOW | graph-driven Evidence-Deep run |
| `qa qa1\|qa2` | QA | quality gate artifacts |

## Default Pattern: Evidence-Deep

```
collect → analyze ⟲ think → synth (survey or report)
```

Final reports are reader-facing publications: internal material IDs, evidence-grade labels, gate names, and OMR workflow terms remain in private working artifacts and are converted to conventional citations and natural professional language.

See [skills/oh-my-research/SKILL.md](skills/oh-my-research/SKILL.md) and [references/REFERENCE.md](skills/oh-my-research/references/REFERENCE.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).

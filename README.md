# Oh-My-Research

**Deep research that ends in a report — not a prototype.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Agent Skills Format](https://img.shields.io/badge/format-Agent%20Skills%201.0-blue)](https://agentskills.io)

Oh-My-Research (OMR) is an Agent Skill that turns papers, web sources, and other materials into **evidence-bound, publication-quality surveys and reports**.

You bring a topic and sources. The skill collects, analyzes with clear evidence boundaries, optionally deepens with structured thinking (first principles, Socratic, triangulation, …), then writes a long-form deliverable chapter by chapter — and exports a polished Word or PDF in your preferred language.

## Vision

Most “research agents” optimize for speed, chat summaries, or code demos. OMR optimizes for something else:

> **High-quality deep research reports grounded in collected materials and evidence.**

That means:

- **Report-first** — the primary outcome is a survey, report, manuscript, or brief readers can trust
- **Evidence-bound** — claims stay within what sources prove, suggest, or only allow you to infer
- **Think before you write** — structured paradigms deepen analysis when confidence is low or gaps are high
- **Publication-safe** — the finished document uses normal citations and prose; workflow jargon stays private
- **Not a coding lab** — no experiment/prototype evaluation path; research stays research

## How it works

One skill. One conversation. It detects what you want (and what the workspace already has), then runs the right step.

```
collect → analyze ⟲ think → synth (survey or report)
```

Analyze and Think form a side-cycle: deepen with structured paradigms when confidence is low or gaps are high, then return to analysis until the judgment is ready for synthesis.

| Phase | What happens |
|-------|----------------|
| **Collect** | Papers, URLs, repos, datasets land in materials + indexes |
| **Analyze** | Brief, evidence map, and judgment — with explicit evidence grades |
| **Think** | Side-cycle on analyze: first principles, red team, steelman, … then back |
| **Synth** | Long survey or report written incrementally, then exported as DOCX or PDF |

Optional paths: capture ideas, take a stance (`decide`), or **reconcile** when new evidence contradicts prior claims.

Default workflow pattern: **Evidence-Deep** (best for literature surveys and structured research reports). Other patterns (rapid brief, idea-first, stance-first, loop) are available when you need them.

## Quick start

### Install

**Claude Code Marketplace**

```text
/plugin marketplace add caesar0301/oh-my-research
/plugin install oh-my-research@oh-my-research
/reload-plugins
```

**npx skills**

```bash
npx skills add caesar0301/oh-my-research
```

### Use it in plain language

Once the skill is loaded, talk naturally — or name an operation:

| You might say | What runs |
|---------------|-----------|
| “Start research on …”, `init "…"` | Bootstrap the workspace |
| Paste a URL / DOI / arXiv / GitHub link, or `collect …` | Add materials |
| “Analyze what we have”, `analyze` | Build evidence + judgment |
| “First principles on the judgment”, `think …` | Deepen the latest artifact |
| “Write the survey / report”, `synth` | Produce the long report |
| “New paper contradicts our claim” | Propose reconcile |

You can also run the full graph-guided flow with `workflow`.

Reports are written **chapter by chapter** (with resume if interrupted), then assembled. Language defaults from your timezone/locale (e.g. `Asia/Shanghai` → Chinese, `Asia/Tokyo` → Japanese), or set `--language` explicitly. Prefer `--format docx` or `pdf` for the deliverable you will share.

## What you get

- A research workspace (`AGENTS.md`, `.omr/` state, materials, indexes, plans)
- Working artifacts: brief, evidence map, judgment (and optional plan / decision / ideas)
- A **self-contained** survey or report under `docs/{survey,report,manuscript,brief}/`
- Professional **Word or PDF** export with cover, TOC, and consistent formatting
- Quality checkpoints before you publish (analyze gate + document lenses + publish gate)

Internal IDs, gate names, and OMR workflow terms stay in private working files. The published document reads like a normal research report.

## Operations at a glance

| Op | Purpose |
|----|---------|
| `init` | Create the research workspace |
| `collect` | Ingest sources into materials + indexes |
| `analyze` | Deep analysis → brief, evidence map, judgment |
| `think [method]` | Structured elicitation on a research artifact |
| `synth` | Incremental long report → Word/PDF |
| `idea` / `decide` | Optional speculation or stance |
| `reconcile` | Repair state when evidence conflicts |
| `workflow` | Graph-driven multi-step run (default Evidence-Deep) |
| `qa` | Run quality-gate checklists |
| `version` | Tag / backup research artifacts |

Details: [`skills/oh-my-research/SKILL.md`](skills/oh-my-research/SKILL.md) · full reference: [`references/REFERENCE.md`](skills/oh-my-research/references/REFERENCE.md)

## Design principles (for users)

1. **Trust auto-detection** — override with a named op when you know the next step
2. **Evidence grades matter** — do not treat “suggests” as “proves”
3. **Deepen when unsure** — use THINK before locking analysis and writing
4. **Long reports are incremental** — outline → chapters → continuity → assemble; resume if needed
5. **Share the document, not the workflow** — the DOCX/PDF should stand alone for its reader

## Development

For contributors working in this repo:

```bash
make help
make format          # python + json + yaml
make check           # CI: format checks + lint
```

Package version lives in [`skills/oh-my-research/SKILL.md`](skills/oh-my-research/SKILL.md) (`metadata.version`); history in [`CHANGELOG.md`](CHANGELOG.md). CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## License

Apache License 2.0 — see [LICENSE](LICENSE).

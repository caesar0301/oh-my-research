# Changelog

All notable changes to the **oh-my-research** skill package are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Single source of truth for the package version: `skills/oh-my-research/VERSION`.
Keep these in sync (use `scripts/skill_version.py`):

- `skills/oh-my-research/VERSION`
- `skills/oh-my-research/SKILL.md` → `metadata.version`
- `.claude-plugin/marketplace.json` → `metadata.version` and `plugins[0].version`

Workspace research tags/backups are separate — see `references/VERSION/version.md`.

## [1.1.1] — 2026-08-18

### Changed

- Fixed: mixed-script rendering — Latin text inside CJK reports keeps a Latin face; DOCX bullets use a real Unicode bullet instead of a Symbol private-use codepoint; Unicode symbols (→ ⇒ ≥ ✓ ✗ ★ ①) route to a wide-coverage system font instead of being dropped or wrongly substituted.

## [1.1.0] — 2026-08-18

### Added

- Skill package version management: `VERSION` file, this changelog, and `scripts/skill_version.py` (`show` / `check` / `sync` / `set` / `bump`).
- Spec-driven DOCX/PDF presentation via LLM-authored `docs/<mode>/_document.json` (`assets/synth/_document.json` starter; `export_report.py --emit-spec`).
- Incremental long-report protocol (`references/SYNTH/long-report.md`) with outline, continuity brief, citation map, and `.omr/report-state.json`.
- `references/LLM-STATE.md` — judgment, gates, outlines, and presentation are LLM-owned; scripts are mechanical only.

### Changed

- `export_report.py` is a thin renderer (no hardcoded styling/structure); presentation decisions live in `_document.json`.
- Removed rigid helpers for init/tree/loop/report-state/methods/QA judgment; agent authors `.omr/` JSON directly.

## [1.0.0] — 2026-08-18

### Added

- Unified `oh-my-research` orchestrator skill (report-first deep research).
- Modes: INIT, COLLECT, ANALYZE, THINK, SYNTH, DECIDE (optional), IDEA, RECONCILE, VERSION (workspace), WORKFLOW, QA.
- Evidence-Deep default pattern with gates A / D / L (optional B); no evaluation/coding path.
- Publication-safe English/Chinese Word and PDF export.
- Graph-guided patterns under `patterns/`.

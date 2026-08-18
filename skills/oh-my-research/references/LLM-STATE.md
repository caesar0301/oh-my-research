# LLM-Driven State & Quality

Judgment, structure, and progress tracking are **agent-owned**. Do not rely on Python helpers to invent chapter plans, pass/fail research quality, or pick thinking methods.

## Principle

| Concern | Owner |
|---------|--------|
| Research judgment, outlines, gates, method choice, continuity | **LLM** following reference docs |
| Report content **and presentation** (title, fonts, colors, cover, TOC, header/footer, chapter order) — via `_document.json` | **LLM** authoring the spec |
| Bytes on disk: DOCX/PDF render from spec, version backups, skill semver sync, optional URL indexing | **Scripts** (`export_report.py`, `version_control.py`, `skill_version.py`, optional `collect_cli.py`) |

`export_report.py` is a **thin renderer**: it applies the LLM-authored `docs/<mode>/_document.json`, not hardcoded styling. It never invents structure or layout — it renders exactly what the spec + chapters describe.

When a scenario differs (short brief, Chinese industry report, 20-theme survey, single-paper deep dive), **adapt the JSON/Markdown artifacts** — do not force a fixed script template.

## Files the agent writes directly

### `.omr/tree-state.json`

Update after each op using unlock rules in `GRAPH.md`. Example shape:

```json
{
  "unlocked": ["init", "collect", "idea", "think"],
  "ready": ["analyze"],
  "locked": ["synth", "decide", "reconcile"],
  "completed": ["init", "collect"]
}
```

Adapt freely: unlock `synth` early for Rapid; keep `decide` locked forever if unused.

### `.omr/loop-state.json`

Only when Loop is active. Agent sets fields from Gate L discussion:

```json
{
  "active": true,
  "mode": "deep-analyze",
  "iteration": 2,
  "focus_question": "…",
  "gaps": ["…"],
  "history": [{"at": "ISO-8601", "event": "iterate", "note": "…"}]
}
```

### `.omr/locale.json`

Preferred report/chat language from timezone (or user override):

```json
{
  "language": "ja",
  "source": "timezone",
  "timezone": "Asia/Tokyo",
  "detected_at": "2026-08-18T20:00:00+09:00"
}
```

BCP-47 tags (`en`, `zh-CN`, `zh-TW`, `ja`, `de`, `pt-BR`, …). See `LANGUAGE.md`. Explicit `--language` always wins over this file.

### `.omr/pattern.json`

```json
{ "name": "Evidence-Deep" }
```

Or any pattern from `patterns/` / user-defined under `.omr/patterns/`.

### `.omr/report-state.json`

Built from the **topic-specific outline**, not a fixed theme-a/b/c list. See `SYNTH/long-report.md`.

### `.omr/quality-gates/QA1-*.json` / `QA2-*.json`

Agent evaluates checklists in `GATES.md` and writes results with rationale — scale thresholds to the research scenario.

## INIT without a script

1. Create `AGENTS.md` from `assets/templates/AGENTS.md.template` (fill placeholders for this topic).
2. Create `.omr/tree-state.json`, `.omr/pattern.json`, and `.omr/locale.json` (timezone→language; see `LANGUAGE.md` / `prefer_language.py --write-workspace`).
3. **Never** pre-create empty `materials/`, `docs/`, `wiki/`, or other content dirs — mkdir only as the parent of a real file write (see `INIT/init.md`).

## THINK without a registry script

1. Read `THINK/methods.md` (and optionally `assets/think/methods.csv` as a catalog).
2. Choose 5 best-fit methods for **this** artifact and user intent.
3. Apply with user confirmation.

## QA (LLM checklist)

1. Read the relevant artifacts.
2. Apply QA1 or QA2 checklist in `GATES.md`; adjust numeric expectations to scope (e.g. a 3-paper deep dive can pass QA1 with an explicit “narrow corpus” rationale).
3. Write JSON under `.omr/quality-gates/` with `status`, `checks[]` (`id`, `status`, `details`), and `rationale` / `scenario_note`.
4. Fail closed on publication-safety and over-claiming; be flexible on coverage counts.

## Report progress (LLM-authored state)

1. After outline approval, write `.omr/report-state.json` mirroring `_outline.md` chapters (topic-specific IDs — not fixed theme-a/b/c).
2. Each turn: set `current`, write chapter file, mark that chapter `done`, prune `_continuity.md`.
3. Resume = read report-state + continue first not-done chapter in `writing_order` (abstract/`00-*` last).

## Presentation spec (LLM-authored)

Before export, write `docs/<mode>/_document.json` (start from `assets/synth/_document.json` or `export_report.py --emit-spec`). Decide, per report/audience/language:

- title / subtitle / author / date; page size + margins; line spacing
- fonts: body + heading Latin, `eastasia` for DOCX CJK, `pdf_cjk` for PDF CJK
- heading colors + sizes; table header color
- `cover` elements + order (or disable); `toc` on/off + depth; `header.text`; `footer.page_numbers`
- `chapters.order` / `include` / `exclude` for publication ordering

Omit any field to accept the neutral default. Never rely on the script to choose styling.

## Still use scripts for

```bash
# Author/refresh the presentation spec (then edit docs/survey/_document.json)
python scripts/export_report.py --emit-spec --mode survey

# Final render — applies the LLM-authored spec (mechanical)
python scripts/export_report.py --mode survey --format docx --language en

# Snapshots / tags (workspace research artifacts)
python scripts/version_control.py tag v1.0

# Skill package semver (from oh-my-research repo root)
python skills/oh-my-research/scripts/skill_version.py check
python skills/oh-my-research/scripts/skill_version.py bump minor --message "…"

# Optional: record a URL into materials/index
python scripts/collect_cli.py "https://arxiv.org/abs/…"
```

`export_report.py` still enforces a mechanical publication-safety scan before writing DOCX/PDF — fix prose if it rejects.

`skill_version.py` syncs package semver only; it does not tag research workspaces.

# SYNTH Mode — Deep Research Report

**Primary deliverable.** Write a self-contained, publication-quality survey/report (or manuscript/brief) from private research artifacts. Preferred output: professionally formatted **Word (`.docx`) or PDF**, in the auto-detected or user-selected language (see `LANGUAGE.md`).

Long deep reports **must not** be generated in a single model turn. Write **incrementally to disk**, one chapter (or chapter section) at a time, then assemble the final document.

Chat replies stay short: progress, paths, and findings — never full chapters.

## Trigger

```
synth
synth --mode survey
synth --mode report
synth --mode manuscript
synth --mode brief
synth --no-wiki
synth --format docx|pdf
synth --language <tag>   # e.g. en, zh-CN, zh-TW, ja, ko, de, fr, es, pt-BR, …
synth --resume
synth --chapter <id>
```

Keywords: report, survey, write up, synthesize, manuscript, brief.

**Requires:** `docs/plans/judgment-*.md` **+ `.omr/quality-gates/gate-a.json` (Gate A pass) + `.omr/quality-gates/gate-p.json` (Gate P pass)**. Decision optional.

### Pre-flight: Phase-Guard Check (v1.3+)

Before starting SYNTH, the agent **must** verify:

1. **`docs/plans/judgment-*.md` exists** — if not, route to ANALYZE first. Show `[PHASE-GUARD]` notice.
2. **`.omr/quality-gates/gate-a.json` exists with `status: "pass"`** — if not, route to ANALYZE → THINK → Gate A first.
3. **`.omr/quality-gates/gate-p.json` exists** — if not, run Gate P first (confirm language/format/mode/audience).
4. **`.omr/tree-state.json` has `synth` in `ready` or `unlocked`** — if `locked`, show `[PHASE-GUARD]` and offer to run prerequisites.

If any prerequisite is missing, **do not silently proceed**. Show the `[PHASE-GUARD]` notice and offer to run the prerequisite stages. If user explicitly insists ("I know, just write the report"), proceed but record `scenario_note: "SYNTH prerequisite skipped by user override"` in the next gate JSON.

### Incremental Writing Enforcement (v1.4 — Gate D check)

**SYNTH must not generate the entire report body in a single model turn.** This is a hard constraint. The agent must:

1. Write `_outline.md` first (one turn)
2. Write `.omr/report-state.json` (same turn as outline)
3. Write **one chapter per turn** under `docs/<mode>/chapters/`
4. Update `report-state.json` after each chapter (mark as `done`)
5. Write executive summary / abstract **last**
6. Run lenses, then Gate D

If the agent detects that it is about to write more than ~2,500 words of report body in a single response, it must **stop and split** the content into chapters. A single-turn full report is a **process violation** — the report may still be usable, but the agent should note the violation and offer to restructure.

**Post-SYNTH structural check (v1.4 — enforced at Gate D):**

Gate D now includes a mandatory `incremental_writing_compliance` check:

| Check | Requirement | If missing |
|---|---|---|
| `chapters_dir` | `docs/<mode>/chapters/` directory exists with ≥1 `.md` file | Gate D **fails** |
| `report_state` | `.omr/report-state.json` exists with `chapters[]` array | Gate D **fails** |
| `outline` | `docs/<mode>/_outline.md` exists | Gate D **warns** |
| `chapter_word_limit` | No single chapter file > 5,000 words | Gate D **warns** (suggest split) |
| `single_file_report` | Report is a single `.md` file with no `chapters/` dir | Gate D **fails** (unless `--mode brief` and < 3,000 words) |

**Exception:** `brief` mode reports under 3,000 words may be written as a single file without `chapters/` — record `scenario_note: "brief mode, single-file under 3K words"` in `gate-d.json`.

If Gate D fails on `incremental_writing_compliance`, the agent must:
1. Split the single-file report into `chapters/*.md` files
2. Create `_outline.md` and `report-state.json` retroactively
3. Re-run Gate D

## Mode defaults

| Pattern | Default `--mode` |
|---------|------------------|
| Evidence-Deep / Evidence-First / Loop | `survey` (or `report` if user asked for report) |
| Stance-First | `report` |
| Idea-First / Rapid | `brief` |

Default `--format`: `docx`. Default language: timezone / `.omr/locale.json` (see `LANGUAGE.md`); explicit `--language` always wins.

## Hard constraint: context-safe writing

Deep reports routinely exceed a single context window. **Mandatory rules:**

1. **Never** draft the entire report body in one response.
2. **Outline first**, then write **one chapter per turn** (or one major section if a chapter is still too large).
3. **Flush each chapter to disk immediately** under `docs/<mode>/chapters/`.
4. Keep a compact **continuity brief** (claims, terms, citation ledger, open threads) — reload that, not all prior chapters.
5. Write **executive summary and conclusions last**, after body chapters exist.
6. **Resume** from `.omr/report-state.json` if interrupted (`synth --resume`).
7. Assemble DOCX/PDF only when all planned chapters are `done`.

Detailed protocol: `long-report.md`.

## Private working layer vs public report

Private artifacts (`docs/plans/`, indexes, continuity brief) may use internal material IDs and evidence grades.

Public chapters and the final DOCX/PDF must **not** expose:

- internal material IDs (`P-001`, `W-002`, …)
- workflow names, gates, QA labels, artifact paths
- internal evidence-grade labels (`proven` / `suggests` / `inferred`)

Translate to conventional citations and natural professional prose. See `long-report.md` § Citation map.

## Language

Resolve once per report (then keep stable) — full policy: `LANGUAGE.md`.

1. Explicit `--language` / user request  
2. `.omr/locale.json` or in-progress `report-state.language`  
3. Research-question / user-message language  
4. **Timezone** → BCP-47 tag (`zh-CN`, `ja`, `de`, `pt-BR`, …; see `LANGUAGE.md`)  
5. OS `LANG` / `LC_*` locale tag  
6. Fallback `en`

Write the full report body in that language. For non-`en` / non-Chinese chrome, set TOC/subtitle in `_document.json`. CJK family (`zh-*`, `ja`, `ko`) needs matching fonts.

Helper: `scripts/prefer_language.py`. `export_report.py` uses the same default when `--language` is omitted.
## Quality bar (before Gate D)

1. All planned chapters on disk; report-state shows complete
2. Claims privately map to evidence; public prose uses conventional citations only
3. Evidence strength expressed naturally (no internal labels)
4. Comparative structure where sources conflict
5. Gaps and limitations mandatory
6. Report is self-contained for a reader without working files
7. Professional, user-friendly tone
8. Per-chapter lenses as needed; whole-document Structure/Prose/Adversarial pass before export
9. Rendered DOCX/PDF inspected; publication-safety scan clean
10. Optional wiki after Gate D (`--no-wiki` to skip)

## Process (summary)

**Gate P first** — confirm language / format / mode / audience / citations before outlining (see `GATES.md`); record once and keep stable.

1. Load judgment + evidence-map + brief + indexes (slim — not wholesale every turn).
2. LLM: outline + citation map + `.omr/report-state.json` adapted to the topic (`long-report.md`, `LLM-STATE.md`).
3. Confirm outline (or quick-pass).
4. Loop: next chapter from report-state → slim context pack → write → save → update continuity → mark done in JSON.
5. Closing chapters; abstract last.
6. Lenses (chapter-scoped, then light global).
7. LLM authors `docs/<mode>/_document.json` (presentation decisions — see below).
8. LLM QA2 → `export_report.py` for DOCX/PDF → inspect → Gate D.
9. Deliver path + short summary; optional wiki.

## Presentation is LLM-driven (not baked into the script)

The exporter is a **thin, spec-driven renderer**. All presentation decisions live in an LLM-authored `docs/<mode>/_document.json`, not in the script:

- **You decide** title / subtitle / author / date, page size + margins, body & heading fonts (Latin + East Asian + PDF CJK), heading colors and sizes, line spacing, cover elements and order, TOC on/off + title + depth, header text, footer page numbers, **attribution** (`Powered by oh-my-research` in the footer; disable via `attribution.enabled=false`), and **chapter order/include/exclude**.
- Start from `assets/synth/_document.json`, or generate a starter: `python scripts/export_report.py --emit-spec --mode <mode>`.
- Any omitted field falls back to a neutral default; CLI `--title`/`--author` override the file for quick runs.
- The script never invents structure or styling — it renders exactly what the spec + chapters say, then runs the publication-safety scan.

Tune the spec to the report: e.g. a Chinese report sets `fonts.body.eastasia` + `fonts.pdf_cjk` and `--language zh-CN`; a brief may set `cover.enabled=false` and `toc.enabled=false`; a manuscript may reorder chapters via `chapters.order`.

**Mixed-script text:** Latin and East Asian faces are bound separately (`latin`/`eastasia`, `pdf_latin`/`pdf_cjk`). Keep a Latin font in `latin`/`pdf_latin` so terms like `Gödel Agent`, `DeepSeek-R1`, and `·` inside Chinese prose render with correct glyphs and spacing. When those fields are omitted, the exporter picks OS-appropriate defaults (macOS / Linux / Windows).

**Unicode symbols:** characters outside both faces (`→ ⇒ ≥ ✓ ✗ ★ ① …`) are routed to a wide-coverage system font discovered from standard font directories on the host OS. On Linux, install `fonts-dejavu` and/or `fonts-noto-core` for best coverage.

## Default deep-survey layout

```
docs/survey/
├── _outline.md
├── _citation-map.md          # private; not exported
├── _continuity.md            # private rolling brief; not exported
├── _document.json            # LLM-authored presentation spec (drives rendering)
├── chapters/
│   ├── 00-title-abstract.md
│   ├── 01-introduction.md
│   ├── 02-background.md
│   ├── 03-theme-a.md
│   ├── 04-theme-b.md
│   ├── 05-theme-c.md         # add themes as outline requires
│   ├── 06-comparative-synthesis.md
│   ├── 07-gaps-and-limitations.md
│   ├── 08-conclusions.md
│   └── 09-references.md
└── deliverables/
    └── <topic>-survey-<lang>.docx|pdf
```

Brief mode may use fewer chapters; manuscript may use journal-style sections. Outline drives the actual file set.

## Final document presentation

Driven by `_document.json` (above). Aim for:

- Descriptive, reader-facing title (never an internal/workflow name)
- Title page, abstract/executive summary, TOC, numbered headings, body, limitations, conclusion, references
- Readable typography, page numbers, consistent hierarchy
- DOCX for editable delivery; PDF for stable distribution

## Chat reply templates

While writing:

```
[SYNTH] Chapter 03/09 done → docs/survey/chapters/03-theme-a.md
Next: 04-theme-b
Progress: 33%
```

When finished:

```
Report: docs/survey/deliverables/<topic>-survey-en.docx
Language: English
Chapters: 9
Key findings: …
Quality review: passed
```

## Hard rules

- No single-shot full-report generation
- No pasting full chapters into chat
- No over-claiming; limitations always present
- No internal IDs / workflow terms in public chapters or export
- Author `_document.json` for presentation — don't rely on the script to choose styling/structure
- Do not export if publication-safety scan fails
- Prefer continuing the chapter loop over rewriting completed chapters

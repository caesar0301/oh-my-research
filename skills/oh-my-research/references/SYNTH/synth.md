# SYNTH Mode — Deep Research Report

**Primary deliverable.** Write a self-contained, publication-quality survey/report (or manuscript/brief) from private research artifacts. Preferred output: professionally formatted **Word (`.docx`) or PDF**, in English or Simplified Chinese.

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
synth --language en|zh-CN
synth --resume
synth --chapter <id>
```

Keywords: report, survey, write up, synthesize, manuscript, brief.

**Requires:** `docs/plans/judgment-*.md`. Decision optional.

## Mode defaults

| Pattern | Default `--mode` |
|---------|------------------|
| Evidence-Deep / Evidence-First / Loop | `survey` (or `report` if user asked for report) |
| Stance-First | `report` |
| Idea-First / Rapid | `brief` |

Default `--format`: `docx`. Default language: user request, else research-question language.

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

- `en` — idiomatic professional English
- `zh-CN` — professional Simplified Chinese
- One primary language per report unless the user requests bilingual

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

- **You decide** title / subtitle / author / date, page size + margins, body & heading fonts (Latin + East Asian + PDF CJK), heading colors and sizes, line spacing, cover elements and order, TOC on/off + title + depth, header text, footer page numbers, and **chapter order/include/exclude**.
- Start from `assets/synth/_document.json`, or generate a starter: `python scripts/export_report.py --emit-spec --mode <mode>`.
- Any omitted field falls back to a neutral default; CLI `--title`/`--author` override the file for quick runs.
- The script never invents structure or styling — it renders exactly what the spec + chapters say, then runs the publication-safety scan.

Tune the spec to the report: e.g. a Chinese report sets `fonts.body.eastasia` + `fonts.pdf_cjk` and `--language zh-CN`; a brief may set `cover.enabled=false` and `toc.enabled=false`; a manuscript may reorder chapters via `chapters.order`.

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

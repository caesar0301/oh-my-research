# SYNTH Mode — Deep Research Report

**Primary deliverable.** Write a self-contained, publication-quality survey/report (or manuscript/brief) from the private research artifacts. The preferred deliverable is a professionally formatted **Word document (`.docx`) or PDF**, in English or Simplified Chinese. Full text goes to disk; chat gets a short summary only.

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
```

Keywords: report, survey, write up, synthesize, manuscript, brief.

**Requires:** `docs/plans/judgment-*.md` (required). Decision optional. Never require evaluation reports.

## Mode defaults

| Pattern | Default `--mode` |
|---------|------------------|
| Evidence-Deep / Evidence-First / Loop | `survey` (or `report` if user asked for report) |
| Stance-First | `report` |
| Idea-First / Rapid | `brief` |

## Private working layer vs public report

Research artifacts under `docs/plans/` may use internal material IDs, evidence grades, gate names, and workflow metadata. These are **private working conventions**.

The report delivered to the reader must not expose:

- `P-001`, `W-002`, `G-003`, or other internal material IDs
- OMR / Oh-My-Research, Evidence-Deep, THINK, SYNTH, Gate A/B/D/L, QA1/QA2
- internal labels such as `proven`, `suggests`, or `inferred`
- implementation notes, workflow status, or artifact paths

Translate internal traceability into conventional reader-facing citations:

- Prefer author–date citations: `(Smith, 2025)` / `（张伟，2025）`
- Numbered citations `[1]` are acceptable for technical reports
- Include a complete references section with author, title, venue/publisher, year, DOI/URL, and access date for web sources
- If metadata is incomplete, resolve it from indexes/materials before export; never print an internal ID as a fallback

Translate evidence grades into natural professional prose. Example: write “A controlled study of 1,200 participants found…” rather than “Evidence grade: proven.”

## Language

- `--language en` → idiomatic professional English
- `--language zh-CN` → professional Simplified Chinese with natural Chinese terminology and punctuation
- If omitted, use the language requested by the user; otherwise use the language of the research question
- Produce one primary language per report unless the user explicitly requests a bilingual edition
- Translate meaning, not sentence structure; preserve technical terms in English in parentheses on first use when useful

## Quality bar (before Gate D)

1. Claims privately map to evidence-map / judgment, but public prose uses conventional citations only
2. Evidence strength is expressed naturally and precisely, without internal labels
3. Comparative structure where literature conflicts (not a flat dump)
4. Open gaps and limitations section **mandatory**
5. The report is self-contained: definitions, context, methods, findings, limitations, and references require no access to working files
6. Tone is professional, direct, and user-friendly; explain specialized concepts before using them
7. Document lenses: Structure → Prose → Adversarial (`GATES.md`)
8. QA2 + Gate D confirm
9. Render and inspect the final DOCX/PDF
10. Optional wiki after Gate D (skip with `--no-wiki`)

## Process

1. Load judgment (+ evidence-map, brief, optional decision, indexes).
2. Choose mode and language; create `docs/<mode>/`.
3. Build a citation map from internal IDs to complete bibliographic entries.
4. Draft reader-facing chapters from templates in `assets/synth/`.
5. Replace every internal material ID with an author–date or numbered citation.
6. Rewrite internal evidence labels as precise natural-language claims.
7. Optional THINK Critique and Refine on the weakest chapter.
8. Run document lenses; apply accepted findings.
9. Export a review copy with `scripts/export_report.py --format docx|pdf --language en|zh-CN`.
10. Inspect the rendered document for typography, page breaks, tables, headings, references, and Chinese glyph coverage. Fix and re-export until clean.
11. Run QA2 on the source and rendered deliverable; present the Gate D checklist.
12. On Gate D pass: deliver the DOCX/PDF and generate wiki unless `--no-wiki`.

## Survey layout (default)

```
docs/survey/
├── 00-overview.md
├── 01-background.md
├── 02-themes.md          # comparative, cited
├── 03-evidence-synthesis.md
├── 04-gaps-and-limitations.md
├── 05-conclusions.md
└── references.md
```

## Report layout

```
docs/report/
├── executive-summary.md
├── findings.md
├── analysis.md
├── recommendations.md    # evidence-bound; not product roadmap unless asked
└── appendix-sources.md
```

## Final document presentation

- Use a descriptive title; do not name the file “OMR report”
- Include title page, executive summary/摘要, table of contents, numbered headings, body, limitations, conclusion, and references
- Use readable typography, page numbers, consistent heading hierarchy, restrained colors, and properly fitted tables
- DOCX is preferred when the user may edit the report; PDF is preferred for stable distribution
- Default output names:
  - English: `docs/<mode>/deliverables/<topic>-<mode>-en.docx|pdf`
  - Chinese: `docs/<mode>/deliverables/<topic>-<mode>-zh-CN.docx|pdf`

## Chat reply template

```
Report: docs/survey/deliverables/<topic>-survey-en.docx
Language: English
Key findings: …
Quality review: passed
```

**Never** paste full chapters into chat.

## Hard rules

- No over-claiming
- No uncitable factual assertions presented as proven
- Limitations and gaps must appear even when confidence is high
- No internal IDs, workflow names, gate names, or evidence-grade labels in public deliverables
- Do not export if the publication-safety scan finds internal terminology

# Long Deep Report Protocol

How to produce long surveys/reports under LLM context limits. Follow this whenever mode is `survey`, `report`, or `manuscript`. `brief` may use a shorter 3–5 chapter variant of the same loop.

## Why

A deep report is often tens of thousands of words. Holding outline + all evidence + all prior chapters in one context causes truncation, repetition, and dropped citations. **Disk is the source of truth**; the model only holds a slim pack per turn.

## Artifacts (on disk)

| File | Public? | Role |
|------|---------|------|
| `docs/<mode>/_outline.md` | no (working) | Chapter plan, word targets, evidence slices |
| `docs/<mode>/_citation-map.md` | no | Internal ID → bibliographic entry + public cite key |
| `docs/<mode>/_continuity.md` | no | Rolling brief: claims, terms, threads, cite ledger |
| `docs/<mode>/chapters/*.md` | yes (body) | Reader-facing chapter files |
| `docs/<mode>/_document.json` | no (working) | LLM-authored presentation spec (drives rendering) |
| `.omr/report-state.json` | no | Progress machine for resume |
| `docs/<mode>/deliverables/*` | yes | Final DOCX/PDF |

Underscore-prefixed working files are **excluded from export content** by `export_report.py` (chapters only). `_document.json` is read as the presentation spec, not rendered as content.

## State machine (LLM-authored)

Write `.omr/report-state.json` yourself from the outline. **Do not** call a fixed chapter-template script. Chapter IDs, counts, and lengths must fit the topic (3 chapters for a brief; 12+ for a large survey).

```json
{
  "mode": "survey",
  "language": "en",
  "format": "docx",
  "title": "Topic-specific title",
  "status": "outlining|writing|closing|exporting|done",
  "chapters": [
    {
      "id": "03-retrieval-mechanisms",
      "path": "docs/survey/chapters/03-retrieval-mechanisms.md",
      "status": "pending|drafting|done|needs_revision",
      "target_words": 1500,
      "purpose": "…",
      "evidence_focus": ["P-001", "P-004"]
    }
  ],
  "writing_order": ["01-…", "02-…", "00-abstract"],
  "current": null,
  "updated_at": "ISO-8601"
}
```

Rules:
- Derive `chapters` from `_outline.md` (slug IDs from real theme names).
- Put abstract/executive-summary ids in `writing_order` **last** (often `00-…`).
- Each turn: set `current`, write the file, set that chapter to `done`, clear `current`, bump `updated_at`.
- Resume: open report-state; continue first not-done id in `writing_order`.

See `LLM-STATE.md`.

## Phase A — Outline (one turn)

Load: research question, judgment summary (not full evidence dump), themes from evidence-map.

Write `docs/<mode>/_outline.md` adapted to **this** research (not a fixed theme-a/b/c skeleton):

1. Title + one-sentence scope
2. Ordered chapter list with purpose, target length, evidence clusters
3. Dependencies (conclusions after themes, abstract last)
4. Writing order note

Confirm with user unless quick-pass. Then write matching `.omr/report-state.json`. Create `docs/<mode>/chapters/` only when writing the first chapter file (and other `docs/<mode>/` files only when writing them).

**Starter shapes (customize freely):**

| Scenario | Shape |
|----------|--------|
| Deep survey | intro → background → N theme chapters → synthesis → gaps → conclusions → references → abstract last |
| Industry report | context → findings → analysis → recommendations → limitations → references → exec summary last |
| Brief | overview → findings → limitations → references → exec summary last |
| Single-paper deep dive | context → method → results reading → critique → implications → references → abstract last |

Split any chapter that would exceed ~2,500 words into `…-part-1` / `…-part-2`.

## Phase B — Citation map (one turn)

From indexes + materials metadata, write `_citation-map.md`:

```markdown
| Internal | Public cite | Full reference |
|----------|-------------|----------------|
| P-001 | (Smith, 2025) | Smith, J. (2025). … DOI |
```

Assign stable public cite keys before body writing. Prefer author–date; numbered `[1]` is fine if the outline chooses that style — stay consistent.

Update the map when new sources appear; never invent bibliographic fields.

## Phase C — Chapter loop (many turns)

For each pending chapter:

### C1. Build slim context pack (only these)

1. Report title, language, mode
2. This chapter’s outline row (purpose, target words, evidence_focus)
3. Full `_continuity.md` (keep it short — see below)
4. **Evidence slice**: excerpts / notes for `evidence_focus` IDs only (from evidence-map + material abstracts). Do not reload the entire evidence-map.
5. Optional: last ~200 words of the **immediately previous** chapter for tone bridge (read from disk; do not reload older chapters)

### C2. Write the chapter

- Reader-facing prose only
- Conventional citations from the map
- Natural evidence-strength wording
- End with a 3–5 bullet **Chapter takeaways** subsection (helps continuity; can be trimmed at export if desired)

Save immediately to `chapters/<id>.md`.

### C3. Update continuity (mandatory, same turn or next)

Edit `_continuity.md` to ≤ ~800–1,200 words total:

```markdown
# Continuity brief

## Thesis so far
…

## Established claims
- Claim … (Smith, 2025)
- Claim … (Li, 2024) — limited sample

## Terms & definitions locked
- Term — definition used in report

## Citation ledger
- (Smith, 2025) — used in ch.01, ch.03
- (Li, 2024) — used in ch.02

## Open threads for later chapters
- Need comparative treatment of X in synthesis
- Limitations: geographic bias

## Avoid repeating
- Do not re-explain Term Y
```

Prune older detail aggressively. Continuity is a **compression layer**, not an archive.

### C4. Mark done

Edit `.omr/report-state.json`: set the chapter `status` to `done`, clear `current`, set `updated_at`. If all done → `status: exporting`.

Chat: one-line progress only. Proceed to next chapter in a **new turn**.

### C5. Oversized chapter

If mid-draft the chapter is still growing:

1. Save part A as `03-theme-a.md`
2. Add `03-theme-a-continued.md` (or split outline into two chapters)
3. Continue with continuity updated — do not keep the unfinished megachapter in context

## Phase D — Closing chapters

Order:

1. Comparative synthesis (reads continuity + theme takeaways only)
2. Gaps and limitations
3. Conclusions
4. References (compile from citation ledger + map; complete entries)
5. Abstract / executive summary / overview (**last** — summarize finished body via continuity + chapter takeaways, not by re-reading all files into context)

## Phase E — Review without reloading everything

1. **Per-chapter lens** (optional): Structure/Prose/Adversarial on the chapter just written, using only that file + continuity.
2. **Global light pass**: skim `_continuity.md` + each chapter’s heading structure (first heading + takeaways), not full text, to catch duplication/order issues.
3. Spot-fix 1–2 weakest chapters if needed (`--chapter <id>`).

## Phase F — Export

First author the presentation spec (this is an LLM decision, not the script's):

```bash
# starter (once); then edit docs/<mode>/_document.json
python scripts/export_report.py --emit-spec --mode survey
```

In `_document.json` set title/subtitle/author, fonts (including `eastasia`/`pdf_cjk` for Chinese), heading colors + sizes, cover elements, TOC depth, header/footer, and `chapters.order`. Omit fields to accept defaults. Then render:

```bash
python scripts/export_report.py --mode survey --format docx --language en
```

The renderer applies `_document.json` and reads `chapters/*.md` only (per spec order, else sorted). Other `_*.md` working files are not included. It never invents styling — tune the spec, not the script.

Then QA2 + Gate D + visual inspect of DOCX/PDF.

## Resume

```
synth --resume
```

1. Read `.omr/report-state.json` and `_outline.md`
2. If `current` is `drafting` with a partial file, finish that chapter
3. Else take the next not-done id from `writing_order`
4. Rebuild slim pack; continue loop

Never restart from outline unless the user asks to re-outline.

## Anti-patterns

| Do not | Do instead |
|--------|------------|
| Generate all chapters in one reply | One chapter per turn |
| Paste full report into chat | Paths + progress only |
| Reload every prior chapter | Continuity brief + previous tail |
| Write abstract first | Write abstract last |
| Expand continuity forever | Cap and prune |
| Export mid-loop | Export when state is complete |
| Dump entire evidence-map each turn | Evidence slice for this chapter |

## Agent turn checklist

```
[ ] report-state + outline loaded (LLM-owned JSON)
[ ] only slim pack in context
[ ] chapter written to chapters/
[ ] continuity updated and pruned
[ ] chapter marked done in report-state.json
[ ] chat: progress line only
[ ] stop turn (next chapter = next turn) unless user asked for quick-pass multi-chapter
```

Quick-pass may write 2–3 short chapters per turn **only if** each is flushed to disk before the next starts and total output stays well within safe limits. Prefer one chapter per turn for deep survey quality.

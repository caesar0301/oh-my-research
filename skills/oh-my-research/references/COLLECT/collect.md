# COLLECT Mode

Passive reception of research materials. User provides sources or search queries; skill delivers files + indexes. After recording a source, **download + convert it to full-text Markdown** so ANALYZE can read the entire paper — not just the abstract.

## Trigger

```
collect <url|doi|arxiv|github|hf|path|"search query">
```

Also: paste of URLs; "search for …"; auto-route from intent detection.

**Init-on-demand:** if no `AGENTS.md` / `.omr/`, run INIT first with inferred topic, then collect.

## Full-Text Conversion (Non-negotiable)

Every convertible source **must** be downloaded and converted to full-text GitHub-Flavored Markdown. The `.source.txt` placeholder alone is insufficient — ANALYZE depends on reading the full paper content.

**Papers layout:** raw binaries go to `materials/papers-raw/<ID>.<ext>`; converted Markdown goes to `materials/papers/<ID>.md` (same stem, different suffix). Other buckets still write `materials/<bucket>/<ID>.md`.

**Conversion chain (try in order, stop at first success):**

| Step | Tool | Handles | When |
|------|------|---------|------|
| 1 (preferred) | **anydoc** (`npx -y @firecrawl/anydoc`) | `.pdf`, `.doc/.docx`, `.ppt/.pptx`, `.xls/.xlsx`, `.odt/.ods/.odp`, `.rtf`, `.epub`, `.csv` | Always try first — best structural fidelity |
| 2 (fallback) | `pymupdf` → `pdfplumber` | `.pdf` text extraction | anydoc unavailable or fails |
| 3 (fallback) | `markdownify` + `beautifulsoup4` | `.html` web pages | anydoc doesn't handle raw HTML |
| 4 (passthrough) | copy | `.md`, `.markdown`, `.txt` | Already Markdown — no conversion needed |

**anydoc availability:** if `npx` is missing or anydoc fails to install, the fallback libraries are used. If all converters fail, record `materials/failed/<ID>.failed.txt` with the reason and continue — do not block other sources.

**Install anydoc if missing:**

```bash
# anydoc needs Node 20+; it is fetched on first run, no install step
npx -y @firecrawl/anydoc --version   # verify
```

**Fallback libraries (optional, install only if anydoc is unavailable):**

```bash
pip install pymupdf pdfplumber markdownify beautifulsoup4
```

Script: `scripts/material_to_markdown.py` — downloads the source (arxiv SDK / DOI redirect / direct URL / local file), converts via the chain above, persists paper binaries to `materials/papers-raw/<ID>.<ext>`, writes Markdown to `materials/papers/<ID>.md` (other buckets: `materials/<bucket>/<ID>.md`), and records failures to `materials/failed/`.

**Batch conversion of pre-downloaded files:** If the user has already downloaded a batch of PDFs (e.g. via `curl`/`wget`) into `materials/papers-raw/` without corresponding `.md` files, use:

```bash
python3 scripts/material_to_markdown.py --convert-dir materials/papers-raw --workspace .
```

This scans the directory for convertible files (`.pdf`, `.docx`, `.html`, etc.) that lack a corresponding `.md` file, and writes Markdown to `materials/papers/<stem>.md`. The material ID is derived from the filename stem (e.g. `2506.23852.pdf` → ID `2506.23852`). Legacy mixed PDFs still sitting in `materials/papers/` convert in place if you pass `--convert-dir materials/papers`.

## Handlers

| Input | Handler | Dest (create only when writing) | Convert to `.md`? |
|-------|---------|------|------|
| arxiv / DOI / PDF paper URL | paper | `materials/papers-raw/<ID>.pdf` + `materials/papers/<ID>.md` | **Yes** — download PDF to `papers-raw`, convert via anydoc |
| Generic http(s) page | web | `materials/web/<ID>.md` | **Yes** — fetch HTML, convert via markdownify |
| github.com/… | github | `materials/github/<ID>.source.txt` | No (repo, not a document) |
| huggingface.co/… | huggingface | `materials/datasets/<ID>.source.txt` | No (dataset/model card) |
| Local file (`.pdf`, `.docx`, …) | paper | `materials/papers-raw/<ID>.<ext>` + `materials/papers/<ID>.md` | **Yes** — copy into `papers-raw`, convert via anydoc |
| Local `.md` / `.txt` | paper/web | `materials/<bucket>/<ID>.md` | Passthrough (already text) |
| Free-text query | search | `materials/search/<ID>.query.txt` | No (query, not a document) |
| Failures | — | `materials/failed/<ID>.failed.txt` | — |

**Do not** pre-create the full `materials/{papers-raw,papers,web,…}` tree. Create only the bucket that receives this source. Index files under `docs/index/` appear when the first index entry is written.

Prefer arxiv SDK / direct PDF when available. Optional Chrome MCP for screenshots of web pages.

Scripts: `scripts/collect_cli.py` (records source + invokes converter) and `scripts/material_to_markdown.py` (download + convert). Routing, naming, depth, and search prioritization are **LLM-driven** per this doc — adapt handlers and destinations to the source type.

## Indexes

Update `docs/index/`:

- `papers-index.json` + `papers-index.md`
- `web-index.json` (optional)
- `github-index.json` (optional)

Assign stable IDs: `P-001`, `W-001`, `G-001`, …

**Index entry fields for converted materials:**

```json
{
  "id": "P-001",
  "source": "https://arxiv.org/abs/1706.03762",
  "title": "Attention Is All You Need",
  "path": "materials/papers-raw/P-001.source.txt",
  "raw_path": "materials/papers-raw/P-001.pdf",
  "markdown_path": "materials/papers/P-001.md",
  "markdown_status": "converted",
  "markdown_method": "anydoc"
}
```

If conversion failed, `markdown_status: "failed"` and `markdown_failure_reason` is set; `markdown_path` is empty. `raw_path` is empty if no binary was written.

## Philosophy

- Deliver materials **with full-text Markdown** — do not over-extract, but do not under-extract either
- Graceful fallback: record failure, continue other inputs
- After successful collect with ≥1 material → run **Gate M** (Materials Sufficiency & Source Diversity) before marking `analyze` ready
- Gate M checks: minimum count, source-type diversity (papers/web/github/datasets/models), topic coverage, recency, obvious gaps, full-text availability
- Gate M shows a **diversity report** to the user and asks: collect more source types or proceed to analyze?
- If a paper conversion failed, warn the user that ANALYZE will run on abstract-only for that paper (degraded mode)
- **Post-collect validation:** after COLLECT, verify that for every convertible file in `materials/papers-raw/`, a corresponding `materials/papers/<stem>.md` exists. If not, offer to run `material_to_markdown.py --convert-dir materials/papers-raw` to batch-convert the missing files. This prevents the common failure mode where sources are downloaded but never converted, and ANALYZE silently runs in degraded (abstract-only) mode.

## Gate M — Source Diversity & Sufficiency Check

After saving materials and updating indexes, run Gate M (see `GATES.md` for full checklist). The gate checks:

1. **Minimum count**: ≥3 materials (or narrow-scope note)
2. **Source-type diversity**: ≥2 distinct buckets (papers, web, github, datasets, models)
3. **Topic coverage**: materials touch ≥2 research sub-questions
4. **Recency**: ≥1 source from last 2 years
5. **Obvious gaps**: no entire sub-question area empty
6. **Full-text Markdown availability**: check `markdown_status` in index

**Show the user a diversity report:**

```
Source Type Inventory:
  papers/    : N items  ✓/⚠/✗
  web/       : N items  ✓/⚠/✗
  github/    : N items  ✓/⚠/✗
  datasets/  : N items  ✓/⚠/✗
  models/    : N items  ✓/⚠/✗
Sub-question coverage: Q1 ✓  Q2 ⚠  Q3 ✗  Q4 ✓
Suggested missing types: [list relevant to topic]
```

**Outcomes:**
- **pass** → mark `analyze` ready in tree-state; recommend `analyze`
- **warn** → suggest specific source types to collect; user decides: collect more or proceed
- **fail** → do not unlock analyze; recommend specific collect actions

Write result to `.omr/quality-gates/gate-m.json`.

## Chat reply

List saved paths, new IDs, conversion status (method used / failures), **Gate M diversity report**, Gate M status, recommended next: `analyze` (if pass) or `collect <suggested sources>` (if warn/fail).

# Design: COLLECT Source Enrichment

| | |
|---|---|
| Status | Draft — pending review |
| Scope | `skills/oh-my-research/references/COLLECT/*`, `scripts/collect_cli.py`, `scripts/material_to_markdown.py`, `references/GATES.md` |
| Deliverable | Broader source-type coverage in COLLECT, feeding Gate M diversity and THINK Source Triangulation with substantive evidence |
| Dependencies | None for classifier/resolver additions; optional `pandoc`, `nbconvert`, search API keys for some enrichment tiers |

---

## 1. Goals & Non-Goals

**Goals**

- Expand the set of source types COLLECT can classify, resolve, and convert to full-text Markdown — without restructuring the bucket-worker / inbox / merge protocol
- Close the gap between Gate M's "source-type diversity" check (which already lists `papers/web/github/datasets/models`) and the thin set of hosts `classify()` actually routes correctly today
- Give THINK's Source Triangulation method real source-type variety to work with, instead of four buckets that are often one host deep (arXiv, generic HTML, github.com stub, query log)
- Keep each enrichment additive: a new classifier branch + resolver + optional converter, not a redesign

**Non-Goals** (tracked separately)

- Full-text search over collected materials (ANALYZE already reads `.md` files directly)
- Automated quality appraisal of new source types (Gate M and evidence grades remain LLM-evaluated)
- A plugin/extension system — enrichments ship in the core `classify()` / resolver / converter code paths
- Replacing anydoc as the preferred converter — new converters are fallbacks in the existing chain

---

## 2. Current State

### 2.1 What COLLECT gathers today

| Bucket | Sources handled | ID prefix | Conversion |
|---|---|---|---|
| **papers** | arXiv, DOI, PDF URLs, local `.pdf/.docx/…` | `P-` | anydoc → pymupdf/pdfplumber → passthrough |
| **web** | generic http(s) HTML pages | `W-` | anydoc → markdownify+bs4 |
| **github** | `github.com/…` URLs (`.source.txt` only — no clone) | `G-` | none |
| **search** | free-text queries (`S-xxx.query.txt`) | `S-` | none |
| **datasets** (opt-in) | `huggingface.co/…` cards | `W-` | none |

### 2.2 The classification bottleneck

Source routing is a single function in `collect_cli.py`:

```python
def classify(source: str) -> str:
    s = source.lower()
    if "arxiv.org" in s or re.match(r"^10\.\d+", s) or s.endswith(".pdf"):
        return "papers"
    if "github.com" in s:
        return "github"
    if "huggingface.co" in s:
        return "datasets"
    if s.startswith(("http://", "https://")):
        return "web"
    return "search"
```

Every source not matching arXiv/DOI/`.pdf`, github.com, or huggingface.co falls into `web` (if a URL) or `search` (otherwise). This misroutes bioRxiv, OpenReview, ACL Anthology, Zenodo, GitLab, PyPI, and most other open repositories into the wrong bucket — losing paper semantics (no `P-` ID, no `papers-raw/` binary, no full-text conversion) or code semantics (no `G-` ID).

### 2.3 The conversion ceiling

`ANYDOC_EXTS` in `material_to_markdown.py` covers office formats and PDF. The fallback chain (pymupdf, pdfplumber, markdownify+bs4) covers PDF and HTML. Common research artifacts outside this set:

- **LaTeX (`.tex`)** — arXiv source bundles
- **Jupyter notebooks (`.ipynb`)** — code + narrative
- **R Markdown (`.Rmd`)** — reproducible reports
- **BibTeX (`.bib`)** — reference lists
- **JATS XML** — PubMed Central's native format

### 2.4 The github stub

The `github` bucket writes only a `.source.txt` stub — no clone, no README extraction, no issue/PR capture. ANALYZE cannot read implementation evidence; it only sees a URL.

### 2.5 The inert search bucket

`bucket-worker.md` instructs the search worker to "run the topic queries" but provides no search tooling — the LLM is expected to improvise. Leftover URLs are pushed to wave 2, but the queries themselves produce no results without an integrated search API.

---

## 3. Enrichment Tiers

Enrichments are ordered by the ratio of evidence-quality impact to implementation effort. Each is additive to the existing architecture.

### Tier 1 — High impact, low effort

#### 3.1 Preprint & repository host patterns

Add host recognition to `classify()` so domain-specific preprint servers route to `papers` instead of `web`:

| Host | Pattern | Bucket | Notes |
|---|---|---|---|
| bioRxiv / medRxiv | `biorxiv.org`, `medrxiv.org` | papers | DOI-resolvable, PDFs downloadable |
| OpenReview | `openreview.net` | papers | API + PDF links |
| ACL Anthology | `aclanthology.org` | papers | stable IDs, BibTeX |
| Zenodo | `zenodo.org` | papers | DOI deposits, PDFs |
| SSRN | `ssrn.com` | papers | social science preprints |
| HAL | `hal.science` | papers | French open archive |
| PsyArXiv / SocArXiv | `*.arxiv.org` OSF preprints | papers | OSF-hosted |

**Implementation:** one-line additions to the `papers` branch of `classify()`; resolver functions in `material_to_markdown.py` mirroring the existing `resolve_arxiv_pdf` pattern (DOI redirect → direct PDF download).

#### 3.2 Repo clone + README extraction

Replace the `.source.txt`-only github handler with a shallow clone + content extraction:

| Step | Action | Output |
|---|---|---|
| 1 | `git clone --depth 1 <repo> <tmp>` | local checkout |
| 2 | Extract `README.md`, `docs/**/*.md`, `*.ipynb` | `materials/github/<ID>.md` (concatenated) |
| 3 | Record repo metadata (stars, license, last commit) | index entry |
| 4 | Clean up tmp checkout | — |

**Other forges** (add to `classify()` github branch): `gitlab.com`, `bitbucket.org`, `codeberg.org`, `sr.ht`.

**Package registries** (new sub-bucket or `github` alias): `pypi.org/project/`, `npmjs.com/package/`, `crates.io/crates/` — fetch package metadata + README via registry API.

#### 3.3 Citation-graph traversal

The biggest structural gap. COLLECT is flat — it collects what the user names plus a topic-seeded search to ~5 papers. No reference following.

| Direction | API | Use |
|---|---|---|
| Forward (citing) | Semantic Scholar `graph/v1/paper/{id}/citations` | "who built on this" |
| Backward (cited) | Semantic Scholar `graph/v1/paper/{id}/references` | "what this is built on" |
| Both | OpenAlex `works/{id}/cited_by` + `referenced_works` | DOI-based, no key required |

**New op:** `collect --expand <ID>` — takes an existing `P-` ID, fetches citing/cited papers, reserves new `P-` IDs, downloads + converts them as a wave-2 batch. Fits the existing inbox/merge protocol without changes.

**Gate M integration:** the diversity report gains a "citation graph coverage" note — whether the corpus is citation-connected or a set of isolated nodes.

### Tier 2 — Medium impact, medium effort

#### 3.4 Search API integration

Make the `search` bucket functional. Currently it only logs queries.

| Backend | Auth | Notes |
|---|---|---|
| Brave Search API | API key | generous free tier |
| DuckDuckGo (html) | none | fragile but free |
| SearXNG (self-hosted) | none | meta-search, privacy-friendly |
| Google Programmable Search | API key | restricted free tier |

**Implementation:** `bucket-worker.md` gains a "execute query via search backend, classify results into other buckets" step. Results flow through `classify()` → appropriate bucket → `--inbox`.

#### 3.5 LaTeX / Jupyter / BibTeX converters

Extend the conversion chain in `material_to_markdown.py`:

| Format | Converter | Placement in chain |
|---|---|---|
| `.tex` | `pandoc` (preferred) or regex stripper (fallback) | after anydoc, before failure |
| `.ipynb` | `nbconvert --to markdown` or direct JSON cell extraction | after anydoc |
| `.Rmd` | `knitr` + `pandoc` | after anydoc |
| `.bib` | `bibtexparser` → reference list markdown | new passthrough tier |
| JATS XML | XSLT or `pubmed-parser` | after anydoc |

All fit the existing fallback pattern: try preferred, fall back, record `.failed.txt` on exhaustion.

#### 3.6 Discussion & community sources

Research synthesis often needs practitioner critique and author commentary — the evidence-boundary system already has `inferred`/`speculative` tiers that fit community signal.

| Source | Conversion path | Evidence grade |
|---|---|---|
| Reddit (r/MachineLearning, etc.) | thread → markdown via `.json` endpoint | inferred |
| Hacker News | Firebase API → markdown | inferred |
| Stack Exchange | API → Q+A markdown | inferred (vetted answers) |
| Twitter/X threads | Nitter/API → markdown | speculative |

**New bucket:** `discussion` (ID prefix `D-`). Gate M diversity report gains a `discussion/` row. ANALYZE's traceability notes flag these as community signal, not peer-reviewed evidence.

### Tier 3 — Lower priority, domain-specific

#### 3.7 Standards, patents, technical reports

| Source | Handler | Notes |
|---|---|---|
| RFCs / IETF | `rfc-editor.org` → text | trivial |
| W3C recommendations | `w3.org/TR/` → HTML → markdown | markdownify path |
| Google Patents | `patents.google.com` → PDF | patent claims structure |
| NIST publications | `nvlpubs.nist.gov` → PDF | tech reports |
| Corporate lab reports | DeepMind, MSR, FAIR blog/PDF | often PDF-only, no DOI |

Add per-topic opt-in; not default buckets.

#### 3.8 Dataset sources beyond HuggingFace

| Source | Access | Notes |
|---|---|---|
| Kaggle | API (kaggle.json) | datasets + notebooks |
| UCI ML Repository | direct download | classic benchmarks |
| Google Dataset Search | schema.org metadata | cross-registry |
| Zenodo / Figshare / Dryad | DOI + API | long-tail scientific data |
| Papers With Code | API | benchmark tables (results ↔ datasets ↔ papers) |

#### 3.9 Multimedia transcripts

| Source | Path | Notes |
|---|---|---|
| YouTube | caption track fetch (`timedtext` API) | conference talks, lectures |
| Podcasts | transcript service (Whisper fallback) | author interviews |
| Webinars | STT pipeline | niche |

anydoc cannot cover audio/video. A transcript worker converts these to the same `materials/<bucket>/<ID>.md` shape ANALYZE reads.

#### 3.10 Structured scientific data

| Source | Format | Notes |
|---|---|---|
| ClinicalTrials.gov | JSON/XML API | trial registries + results |
| Cochrane | HTML | pre-appraised systematic reviews |
| OpenAlex works/authors/institutions | JSON API | metadata enrichment (ORCID, affiliations, citation counts) |

OpenAlex metadata can enrich ANALYZE traceability notes without a new bucket — augment existing index entries.

---

## 4. Architecture: Why This Fits

The COLLECT design is extensible by construction. Each enrichment is a new classifier branch + resolver + optional converter — not a redesign.

```
User source
     │
     ▼
 classify()  ────►  bucket assignment  (add host patterns here)
     │
     ▼
 bucket-worker  ──►  resolve + download  (add resolvers in material_to_markdown.py)
     │
     ▼
 conversion chain  ──►  anydoc → fallbacks → .failed.txt  (add converters here)
     │
     ▼
 --inbox  ──►  docs/index/inbox/<ID>.json
     │
     ▼
 --merge-inbox  ──►  papers-index.json
     │
     ▼
 Gate M  (diversity report gains rows for new source types)
```

| Layer | What changes | What stays |
|---|---|---|
| `classify()` | New host patterns per bucket | Single-function routing; ID prefix scheme |
| `material_to_markdown.py` | New resolver functions + converter fallbacks | anydoc-first chain; `papers-raw/` + `papers/` layout |
| `bucket-worker.md` | Per-source discovery instructions; search API step | One worker per bucket; inbox/merge protocol; reserved IDs |
| `GATES.md` Gate M | Diversity report gains `preprints`, `code-impl`, `discussion`, `standards` rows | LLM-evaluated; pass/warn/fail outcomes |
| Pattern JSON | No changes — `collect → analyze` edge and Gate M are source-agnostic | Evidence-Deep default; gate chain |

---

## 5. Gate M Diversity Report (Proposed Extension)

Current diversity report:

```
Source Type Inventory:
  papers/    : N items  ✓/⚠/✗
  web/       : N items  ✓/⚠/✗
  github/    : N items  ✓/⚠/✗
  search/    : N items  ✓/⚠/✗
  datasets/  : N items  ✓/⚠/✗
  models/    : N items  ✓/⚠/✗
```

Proposed extended report:

```
Source Type Inventory:
  papers/        : N items  ✓/⚠/✗
  preprints/     : N items  ✓/⚠/✗   (bioRxiv, OpenReview, SSRN, …)
  web/           : N items  ✓/⚠/✗
  github/        : N items  ✓/⚠/✗
  code-impl/     : N items  ✓/⚠/✗   (PyPI, npm, Papers With Code)
  search/        : N items  ✓/⚠/✗
  datasets/      : N items  ✓/⚠/✗
  models/        : N items  ✓/⚠/✗
  discussion/    : N items  ✓/⚠/✗   (Reddit, HN, Stack Exchange)
  standards/     : N items  ✓/⚠/✗   (RFCs, W3C, NIST)
  patents/       : N items  ✓/⚠/✗
  multimedia/    : N items  ✓/⚠/✗   (talks, podcasts)
Citation graph: connected / sparse / isolated
Sub-question coverage: Q1 ✓  Q2 ⚠  Q3 ✗  Q4 ✓
Suggested missing types: [list relevant to topic]
```

New rows are additive — Gate M warns when a relevant type is empty without opt-out, same as the current four-bucket check.

---

## 6. Implementation Priority

| Priority | Enrichment | Rationale | Effort | Dependencies |
|---|---|---|---|---|
| **P0** | Preprint host patterns (§3.1) | One-line `classify()` additions; fixes misrouting of bioRxiv/OpenReview/etc. | Low | None |
| **P0** | Repo clone + README extraction (§3.2) | `github` bucket is currently a stub; ANALYZE can't read implementation evidence | Low-Medium | `git` (ubiquitous) |
| **P1** | Citation-graph traversal (§3.3) | Strengthens Gate M diversity + THINK Source Triangulation — the two quality mechanisms already enforced | Medium | Semantic Scholar / OpenAlex API (no key for OpenAlex) |
| **P1** | LaTeX / Jupyter / BibTeX converters (§3.5) | Common in arXiv-adjacent collection; fits existing fallback chain | Low-Medium | `pandoc`, `nbconvert` (optional) |
| **P2** | Search API integration (§3.4) | Makes `search` bucket functional instead of a query log | Medium | Search API key |
| **P2** | Discussion sources (§3.6) | Fills "practitioner critique" evidence tier; needs thread→md converter | Medium | None |
| **P3** | Standards, patents, tech reports (§3.7) | Domain-specific; per-topic opt-in | Medium | None |
| **P3** | Dataset sources beyond HF (§3.8) | Expands opt-in `datasets` bucket | Medium | Per-registry API keys |
| **P3** | Multimedia transcripts (§3.9) | Useful but niche; anydoc can't help | Medium | STT dependency |
| **P3** | Structured scientific data (§3.10) | Metadata enrichment; niche full-text | Medium | Per-source API |

---

## 7. Open Questions

1. **Bucket granularity**: Should preprints be a sub-type of `papers` (same `P-` prefix, distinguished by `source_type` field in the index) or a separate bucket with its own prefix? Separate buckets make Gate M diversity reports clearer; sub-types keep the ID scheme simpler.

2. **Citation-graph depth**: Should `collect --expand` follow citations recursively (with a depth cap) or only one hop? Recursive traversal risks corpus explosion; one hop may be too shallow for Source Triangulation's "≥3 independent source types" requirement.

3. **Discussion evidence grading**: Should community sources get a dedicated evidence grade between `inferred` and `speculative`, or reuse `inferred` with a traceability note flagging them as non-peer-reviewed?

4. **Search backend default**: Which search API should be the zero-config default (no API key required)? DuckDuckGo HTML scraping is fragile but free; SearXNG requires self-hosting.

5. **Converter availability checks**: Should `material_to_markdown.py` probe for `pandoc`/`nbconvert` at startup and record availability, or check per-source as in the current anydoc pattern?

---

## 8. Non-Goals Reiterated

- No plugin/extension system — enrichments ship in core code paths
- No automated quality appraisal — Gate M and evidence grades stay LLM-evaluated
- No full-text search over collected materials — ANALYZE reads `.md` files directly
- No replacement of anydoc as the preferred converter — new converters are fallbacks
- No restructuring of the bucket-worker / inbox / merge protocol — enrichments are additive

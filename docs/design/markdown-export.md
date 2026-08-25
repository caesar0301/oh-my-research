# Design: Markdown Deliverable Export (`--format md`)

| | |
|---|---|
| Status | Approved for implementation |
| Scope | `skills/oh-my-research/scripts/export_report.py`, `references/SYNTH/*`, `SKILL.md` |
| Deliverable | Single self-contained Markdown report with Mermaid figures and GFM tables |
| Dependencies | None (pure stdlib; no new requirements) |

---

## 1. Goals & Non-Goals

**Goals**

- `export_report.py --format md` produces a publication-safe, single-file Markdown deliverable
- Figures are authored as **Mermaid fenced code blocks**; tables as **GFM tables** — both pass through byte-for-byte
- The Markdown renderer is a peer of `export_docx` / `export_pdf`: same signature, same spec (`_document.json`) resolution, same publication-safety gate
- Malformed Mermaid blocks fail the export loudly instead of silently rendering blank on the reader side

**Non-Goals** (tracked separately)

- Rendering Mermaid to images inside DOCX/PDF (optional `mmdc` enhancement)
- Embedding static images (`![]()`), figure asset directories, or link checking
- Figure numbering automation — captions are authored by the agent

---

## 2. Architecture

The exporter stays a **thin, spec-driven renderer**. Markdown reuses the entire existing front half; only the byte-writing tail is new.

```
chapters/*.md ──► assemble() ──► validate_publication() ──► resolve_spec() ──┬─ export_docx(chapters, output, spec, language)
  (agent-written,                                                          │
   Mermaid + GFM                chapter selection / ordering /              ├─ export_pdf  (chapters, output, spec, language)
   pass-through                 front-matter stripping                       │
   content)                     publication-safety scan                      └─ export_md   (chapters, output, spec, language)   ← NEW
```

| Shared stage | Markdown behavior |
|---|---|
| `assemble()` | Reused verbatim — chapter `order` / `include` / `exclude` from the spec already apply |
| `validate_publication()` | Reused verbatim — runs **before** format dispatch, so the `.md` deliverable is gated like any other |
| `resolve_spec()` | Reused verbatim — presentation fields without Markdown semantics (`fonts`, `colors`, `page`, `line_spacing`) are silently ignored |
| Output naming | Reused verbatim — `deliverables/{topic}-{mode}-{language}.md` falls out of the existing `args.format` interpolation |

---

## 3. Renderer: `export_md()`

### 3.1 Placement & Signature

New `# MARKDOWN` section in `export_report.py`, after the `# PDF` section, before `# Spec resolution + CLI`. Signature is structurally identical to the sibling renderers:

```python
def export_md(
    chapters: list[tuple[str, str]],   # (filename, raw markdown) — already ordered by spec
    output: Path,
    spec: dict[str, Any],
    language: str,
) -> None:
```

### 3.2 Processing Pipeline

| Step | Action | Spec field consumed |
|---|---|---|
| 1 | Emit YAML front-matter (title, subtitle, author, date, lang) | `title` / `subtitle` / `author` / `date` / `cover.elements` |
| 2 | Emit title block: `# title`, subtitle, author, date lines | `cover.elements` |
| 3 | Build TOC from chapter headings as a static anchor list (GitHub-style anchors; depth-capped) | `toc.enabled` / `toc.title` / `toc.depth` |
| 4 | Append chapter bodies verbatim, separated by `\n\n---\n\n`; drop a first-chapter H1 that duplicates the title | `drop_first_h1_matching_title` |
| 5 | Run Mermaid lint across the assembled body (see §4.2); fail closed | — |
| 6 | Append attribution footer line | `attribution.enabled` / `attribution.text` |
| 7 | Write atomically to `output` (parent dirs created on demand) | — |

### 3.3 Skeleton

```python
# --------------------------------------------------------------------------- #
# MARKDOWN
# --------------------------------------------------------------------------- #
GITHUB_ANCHOR_RE = re.compile(r"[^\w\u3400-\u9fff\s-]")

MERMAID_TYPES = (
    "graph", "flowchart", "sequenceDiagram", "classDiagram",
    "stateDiagram-v2", "stateDiagram", "erDiagram", "journey",
    "gantt", "pie", "mindmap", "timeline", "quadrantChart", "gitGraph",
)


def github_anchor(text: str) -> str:
    """GitHub-style heading anchor: lowercase, strip punctuation, spaces to '-'."""
    slug = GITHUB_ANCHOR_RE.sub("", text.strip().lower())
    return re.sub(r"\s+", "-", slug)


def lint_mermaid(body: str) -> list[str]:
    """Structural lint for fenced Mermaid blocks; returns violation messages."""
    findings: list[str] = []
    fence = re.compile(r"^```mermaid\s*$", re.MULTILINE)
    for i, match in enumerate(fence.finditer(body), start=1):
        # 1. Block must close before the next opening fence or EOF.
        close = body.find("\n```", match.end())
        if close == -1:
            findings.append(f"mermaid block #{i}: unclosed fence")
            continue
        block = body[match.end():close]
        # 2. First non-empty line must declare a known diagram type.
        first = next((ln.strip() for ln in block.splitlines() if ln.strip()), "")
        if not first.lower().startswith(MERMAID_TYPES):
            findings.append(f"mermaid block #{i}: unknown diagram type {first!r}")
    return findings


def export_md(
    chapters: list[tuple[str, str]],
    output: Path,
    spec: dict[str, Any],
    language: str,
) -> None:
    """Render chapters to a single self-contained Markdown deliverable."""
    parts: list[str] = []

    # 1. YAML front-matter for static site generators and metadata readers.
    parts.append(front_matter(spec, language))

    # 2. Title block mirroring the cover semantics of DOCX/PDF.
    parts.append(title_block(spec, language))

    # 3. Static TOC — portable across GitHub/GitLab/Typora, unlike [TOC] markers.
    if spec["toc"].get("enabled", True):
        parts.append(toc_block(chapters, spec, language))

    # 4. Chapter bodies verbatim: GFM tables and Mermaid fences pass through
    #    unchanged; only a duplicated leading H1 is dropped (spec-controlled).
    parts.extend(chapter_bodies(chapters, spec))

    # 5. Attribution footer replaces the DOCX/PDF page footer.
    credit = attribution_label(spec)
    if credit:
        parts.append(f"\n---\n\n*{credit}*")

    # 6. Fail closed on malformed Mermaid before anything is written.
    body = "\n\n".join(parts)
    findings = lint_mermaid(body)
    if findings:
        raise SystemExit(
            "Mermaid lint failed:\n"
            + "\n".join(f"  - {f}" for f in findings)
        )

    # 7. Atomic write; deliverables/ appears only when a file lands in it.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body.rstrip() + "\n", encoding="utf-8")
```

Helpers `front_matter`, `title_block`, `toc_block`, `chapter_bodies` are private module-level functions (~10–20 lines each) living in the same section. `attribution_label()` is reused from the PDF path.

### 3.4 CLI Wiring

```python
# main() — argument stays a single-choice flag; no subcommands.
parser.add_argument("--format", default="docx", choices=["docx", "pdf", "md"])

# main() — dispatch gains one branch, order: docx, pdf, md.
if args.format == "docx":
    export_docx(chapters, output, spec, language)
elif args.format == "pdf":
    export_pdf(chapters, output, spec, language)
else:
    export_md(chapters, output, spec, language)
```

---

## 4. Mermaid Figures

### 4.1 Authoring Conventions (specification layer)

Figures are agent-authored chapter content — the renderer only transports them. The writing protocol in `references/SYNTH/long-report.md` gains a **Figures** section:

- **All figures are Mermaid fenced blocks** — no ASCII art, no external images
  - `flowchart` for structures and pipelines; `sequenceDiagram` for interactions
  - `classDiagram` / `stateDiagram-v2` / `erDiagram` for static models
  - `pie` / `mindmap` / `timeline` for summaries
- **Caption**: one italic line immediately below the fence — `*Figure 3-1: ...*` (manual `chapter-sequence` numbering)
- **Node IDs** must not match `[PWGSE]-\d+` (e.g. `P-001`) — the publication-safety scan treats that pattern as an internal material ID and blocks the export; use `N1`, `N2`, or short semantic names
- **Labels** inside nodes/edges follow the report language; keep each label short enough to survive reader-side auto-layout

### 4.2 Transport & Lint

- Markdown output passes fences through byte-for-byte — GitHub, GitLab, Typora, Obsidian, and MkDocs render them natively
- `lint_mermaid()` (skeleton §3.3) enforces the two failure modes that render as silent blanks: unclosed fences and unknown diagram types
- Lint runs **after assembly, before write** (step 6 of the pipeline) so a failure leaves no partial deliverable on disk

### 4.3 Degradation Semantics (DOCX / PDF)

DOCX and PDF paths are **unchanged**. A Mermaid fence enters the existing `code` branch of `markdown_blocks()` and renders as a monospaced, shaded source block. This is the documented behavior:

> Figures render graphically in the Markdown deliverable. In DOCX/PDF exports, Mermaid blocks appear as source code; consult the Markdown version for rendered figures.

---

## 5. Specification Layer Updates

| File | Change |
|---|---|
| `references/SYNTH/synth.md` | Usage line → `--format docx\|pdf\|md`; Gate D gains a Markdown check (lint clean, anchors resolve); §4.3 degradation note |
| `references/SYNTH/long-report.md` | New **Figures** section with the authoring conventions from §4.1 |
| `SKILL.md` | SYNTH mode row and Dependencies paragraph mention the Markdown deliverable |
| `scripts/export_report.py` | Docstring: “renders bytes (DOCX via python-docx, PDF via reportlab, Markdown via stdlib)” |
| `assets/synth/_document.json` | No change — spec fields without Markdown semantics are ignored by design |

---

## 6. Output Conventions

| Aspect | Convention |
|---|---|
| Path | `docs/<mode>/deliverables/{topic}-{mode}-{language}.md` (existing naming, `.md` extension) |
| Self-containment | Single file — Mermaid and tables are text, so no sidecar assets |
| Encoding | UTF-8, trailing newline |
| Chapter separator | `\n\n---\n\n` horizontal rule between chapters |
| Anchors | GitHub dialect (lowercase, strip punctuation, spaces → `-`, CJK preserved) |

---

## 7. Security & Quality Gates

| Gate | Mechanism | Markdown delta |
|---|---|---|
| Publication safety | `validate_publication()` runs pre-dispatch | None — inherited; Mermaid content is scanned like any prose (hence the node-ID naming rule) |
| Mermaid lint | `lint_mermaid()` inside `export_md` | New, fail-closed |
| Gate D (QA2) | Agent-side checklist | Visual DOCX/PDF inspection is replaced by: lint clean + TOC anchors resolve + front-matter complete |
| Command execution | None | The renderer spawns no subprocesses and performs no network I/O |

---

## 8. Test Plan

| # | Case | Expected |
|---|---|---|
| 1 | Workspace with Chinese title, 3 chapters, GFM tables, `flowchart` + `sequenceDiagram` | `.md` generated; front-matter, TOC anchors, tables, fences intact |
| 2 | Chapter containing `P-001` prose | Export blocked by publication-safety scan (unchanged behavior) |
| 3 | Unclosed Mermaid fence | Export aborts with `Mermaid lint failed`, no file written |
| 4 | Fence whose first line is not a diagram type | Same as #3 |
| 5 | First chapter H1 identical to spec title | H1 dropped; second-level headings unaffected |
| 6 | Same workspace exported with `--format docx` | Identical to pre-change output (regression) |
| 7 | `attribution.enabled = false` | No footer line |

Fixture: throwaway workspace under `/tmp/omr-test` with `docs/survey/chapters/*.md` plus a hand-written `_document.json`.

---

## 9. Out of Scope

- `mmdc`-based Mermaid rasterization for DOCX/PDF (optional dependency, graceful degradation)
- Static image embedding (`![]()`) with figure directories and link checking
- Automated figure/table numbering

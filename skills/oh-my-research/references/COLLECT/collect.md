# COLLECT Mode

Passive reception of research materials. User provides sources or search queries; skill delivers files + indexes. Minimal parsing (format/metadata only) — no deep semantic analysis (that is ANALYZE).

## Trigger

```
collect <url|doi|arxiv|github|hf|path|"search query">
```

Also: paste of URLs; “search for …”; auto-route from intent detection.

**Init-on-demand:** if no `AGENTS.md` / `.omr/`, run INIT first with inferred topic, then collect.

## Handlers

| Input | Handler | Dest (create only when writing) |
|-------|---------|------|
| arxiv / DOI / PDF paper URL | paper | `materials/papers/<file>` |
| Generic http(s) page | web | `materials/web/<file>` |
| github.com/… | github | `materials/github/<file>` |
| huggingface.co/… | huggingface | `materials/datasets/<file>` or models note in index |
| Free-text query | search | prioritize downloads into papers/web; log in `materials/search/<file>` |
| Failures | — | `materials/failed/<file>` with reason |

**Do not** pre-create the full `materials/{papers,web,…}` tree. Create only the bucket that receives this source. Index files under `docs/index/` appear when the first index entry is written.

Prefer arxiv SDK / direct PDF when available. Optional Chrome MCP for screenshots of web pages.

Scripts: optional `scripts/collect_cli.py` for recording a URL into `materials/` + index (creates parent dirs only for files it writes). Routing, naming, depth, and search prioritization are **LLM-driven** per this doc — adapt handlers and destinations to the source type.

## Indexes

Update `docs/index/`:

- `papers-index.json` + `papers-index.md`
- `web-index.json` (optional)
- `github-index.json` (optional)

Assign stable IDs: `P-001`, `W-001`, `G-001`, …

## Philosophy

- Deliver materials; do not over-interpret
- Graceful fallback: record failure, continue other inputs
- After successful collect with ≥1 paper → mark `analyze` **ready** in tree-state

## Chat reply

List saved paths, new IDs, failures, recommended next: `analyze`.

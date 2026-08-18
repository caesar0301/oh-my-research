# COLLECT Mode

Passive reception of research materials. User provides sources or search queries; skill delivers files + indexes. Minimal parsing (format/metadata only) — no deep semantic analysis (that is ANALYZE).

## Trigger

```
collect <url|doi|arxiv|github|hf|path|"search query">
```

Also: paste of URLs; “search for …”; auto-route from intent detection.

**Init-on-demand:** if no `AGENTS.md` / `.omr/`, run INIT first with inferred topic, then collect.

## Handlers

| Input | Handler | Dest |
|-------|---------|------|
| arxiv / DOI / PDF paper URL | paper | `materials/papers/` |
| Generic http(s) page | web | `materials/web/` |
| github.com/… | github | `materials/github/` |
| huggingface.co/… | huggingface | `materials/datasets/` or models note in index |
| Free-text query | search | prioritize downloads into papers/web; log in `materials/search/` |
| Failures | — | `materials/failed/` with reason |

Prefer arxiv SDK / direct PDF when available. Optional Chrome MCP for screenshots of web pages.

Scripts: `scripts/collect_cli.py` (orchestrates handlers).

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

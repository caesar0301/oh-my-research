# OMR Scripts

> Load when: invoking any mechanical script — flags, defaults, examples. Depth: lean.

**Scripts are mechanical only.** Research judgment, outlines, gate quality checks, THINK method choice, and progress tracking are LLM-driven. `gate_cli.py` is the narrow exception: it validates gate mode, confirmation fields, and chain order without judging quality — see `references/GATES.md` and `references/LLM-STATE.md`.

Development tests live at repo root `tests/`, and repo-maintenance scripts (`skill_lint.py`, `skill_version.py`) live at repo root `scripts/`; this `skills/oh-my-research/` directory is the production skill package and must contain only what the agent runs inside a research workspace. Run tests with `make test`, maintenance lint with `make skill-lint`.

| Script | Role |
|--------|------|
| `gate_cli.py` | Persist `.omr/gate-mode.json` (`init`), change mode only from an explicit user request (`set`), write gate JSONs with confirmation fields (`record`), and validate mode/chain/confirmations before ANALYZE / SYNTH / export (`validate`). Never judges research quality. Default `--workspace` is `<cwd>/_omr`. |
| `export_report.py` | Thin, spec-driven renderer: applies the LLM-authored `docs/<mode>/_document.json` to turn `chapters/` into publication-safe DOCX/PDF/Markdown. No hardcoded styling. The Markdown deliverable passes Mermaid figures and GFM tables through verbatim. Default output is the public hand-off `<workspace>/deliverables/<topic>-<mode>-<language>.<format>` (`--output` overrides; `--workspace` defaults to `<cwd>/_omr`). Default `--language` follows timezone/workspace via `prefer_language.py`. |
| `prose_lint.py` | Native-expression linter: detects translationese — calqued metaphors, English-derived coinages, article-style CJK headings (一个…), wrong measure words, 的-chains, passive/em-dash stacking, over-long sentences. Reports per-file budgets (avg sentence length, dash/1k, passive/1k). Exit 1 on `high` findings; `--strict` also fails on `medium`; allowlist via `--allow` or `_omr/.omr/prose-lint-allow.txt`. |
| `prefer_language.py` | Detect preferred BCP-47 language from timezone/locale; optional `.omr/locale.json` write; `--list` dumps timezone map |
| `version_control.py` | Workspace research tags and backups (`<active-workspace>/.omr/versions/`, `<active-workspace>/.omr/backups/`); covers `docs/plans`, synth draft dirs, and `deliverables/` (all under the active workspace) |
| `skill_version.py` | Skill-package semver: `show` / `check` / `sync` / `set` / `bump` against `SKILL.md` (+ marketplace + `CHANGELOG.md`) |
| `collect_cli.py` | Record a URL/query into `_omr/materials/` + index (creates only parent dirs of files written). `--convert` (default on) invokes `material_to_markdown.py`. Parallel COLLECT: `--id` + `--bucket` + `--inbox` writes `_omr/docs/index/inbox/<ID>.json` without touching `papers-index.json`; `--merge-inbox` appends inbox files into the index (skips duplicate IDs). |
| `material_to_markdown.py` | Download a source (arXiv / DOI / preprint hosts: ACL Anthology, bioRxiv, medRxiv, OpenReview, Zenodo, SSRN, HAL / direct URL / local file) and convert it to GitHub-Flavored Markdown. Papers persist the binary at `_omr/materials/papers-raw/<ID>.<ext>` and write Markdown at `_omr/materials/papers/<ID>.md` (same stem); other buckets write `_omr/materials/<bucket>/<ID>.md`. Uses **anydoc** (`npx -y @firecrawl/anydoc`, Node 20+) as the preferred converter, with `pymupdf` → `pdfplumber` (PDF), `markdownify` (HTML), and `beautifulsoup4` as fallbacks; `--index` batch-converts/retries every indexed source lacking a `.md`, `--convert-dir` batch-converts pre-downloaded files. Markdown/`.txt` files pass through unchanged. Failures are recorded to `_omr/materials/failed/<ID>.failed.txt`. |
| `report_lint.py` | **(v1.4)** Publication-safety linter: scans report chapters **and the `_document.json` presentation spec (title/subtitle/author/header/footer string fields)** for internal material IDs, raw arXiv IDs, evidence-grade labels, workflow jargon, gate names, private paths, THINK ledger references, and outcome stamps. Exit 0 = clean, 1 = violations found. Use before Gate D to catch leaked internal terminology. |

Repo-maintenance tools (skill-package semver `skill_version.py`, structure lint `skill_lint.py`) live at the **repo root** in `scripts/` — they are not part of the installed skill package.

Install export dependencies (macOS or Linux):

```bash
python3 -m pip install -r scripts/requirements.txt
```

**Linux PDF symbol coverage** (optional but recommended):

```bash
# Debian/Ubuntu
sudo apt-get install -y fonts-dejavu fonts-noto-core fonts-noto-cjk
# Fedora
sudo dnf install -y dejavu-sans-fonts google-noto-sans-fonts google-noto-sans-cjk-fonts
```

PDF CJK text uses reportlab's built-in CID fonts (`STSong-Light`, etc.) and needs no system Chinese fonts. DOCX East Asian face names default to `Noto Sans CJK SC` on Linux / `PingFang SC` on macOS / `Microsoft YaHei` on Windows — override in `_document.json` if needed.

All scripts use `#!/usr/bin/env python3` and the stdlib `pathlib` API; they are intended to run unchanged on macOS and Linux.
Examples. All scripts default `--workspace` to `<cwd>/_omr`, which is the **default working root (container)**. When a topic lives in a subdirectory, pass that topic root explicitly: `--workspace _omr/<topic-slug>`. Scripts never resolve or create topic roots themselves; the agent does that first (see `SKILL.md` § Workspace resolution). `prefer_language.py` is the exception: `--workspace` is read-only there; use `--write-workspace <topic-root>` to write `.omr/locale.json`.

```bash
# 1. Author/refresh the presentation spec, then edit _omr/docs/<mode>/_document.json
python3 scripts/export_report.py --emit-spec --mode survey

# 2. Render, applying that spec
python3 scripts/export_report.py --mode survey --format docx --language en
python3 scripts/export_report.py --mode report --format pdf --language zh-CN
python3 scripts/version_control.py tag v1.0
python3 scripts/collect_cli.py "https://arxiv.org/abs/…"
python3 scripts/collect_cli.py "https://arxiv.org/abs/…" --no-convert   # index only, no download/convert
python3 scripts/collect_cli.py "https://arxiv.org/abs/…" --id P-001 --bucket papers --inbox
python3 scripts/collect_cli.py --merge-inbox
python3 scripts/material_to_markdown.py "https://arxiv.org/abs/…" --id P-001
python3 scripts/material_to_markdown.py --index            # convert all indexed sources lacking .md
python3 scripts/material_to_markdown.py --convert-dir _omr/materials/papers-raw   # batch convert raw PDFs → _omr/materials/papers/<stem>.md
python3 scripts/collect_cli.py "https://arxiv.org/abs/…" --workspace _omr/veya-tracing   # explicit topic root
python3 scripts/gate_cli.py init --workspace _omr/veya-tracing
python3 scripts/gate_cli.py set --workspace _omr/veya-tracing --mode quick-pass --user-request "no confirmations"
python3 scripts/gate_cli.py record --workspace _omr/veya-tracing --gate M --decision-source user --user-decision "proceed" --checks '[{"id":"coverage","status":"pass","details":"ok"}]'
python3 scripts/gate_cli.py validate --workspace _omr/veya-tracing --stage analyze
python3 scripts/report_lint.py --mode survey               # (v1.4) lint report chapters
python3 scripts/report_lint.py --file _omr/docs/survey/my-report.md --json     # (v1.4) lint a single file, JSON output
```

`version_control.py` tags research workspaces only. Skill-package semver is repo maintenance (`scripts/skill_version.py` at the repo root) — see `references/VERSION/version.md`.

Long reports: the agent writes `<active-workspace>/.omr/report-state.json`, `<active-workspace>/docs/<mode>/chapters/`, and `<active-workspace>/docs/<mode>/_document.json` per `references/SYNTH/long-report.md`, then calls `export_report.py --workspace <active-workspace>`. Presentation (fonts, cover, TOC, colors, chapter order) is decided in `_document.json`, not the script. Working `_*.md` files are not exported (`_document.json` is read but not rendered as content).

`export_report.py` refuses unsafe internal terminology at render time — fix prose and retry.

Python 3.10+ recommended.

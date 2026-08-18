# OMR Scripts

**Scripts are mechanical only.** Judgment, outlines, gates, THINK method choice, and progress tracking are LLM-driven — see `references/LLM-STATE.md` and `references/GATES.md`.

| Script | Role |
|--------|------|
| `export_report.py` | Thin, spec-driven renderer: applies the LLM-authored `docs/<mode>/_document.json` to turn `chapters/` into publication-safe DOCX/PDF. No hardcoded styling. Default `--language` follows timezone/workspace via `prefer_language.py`. |
| `prefer_language.py` | Detect preferred BCP-47 language from timezone/locale; optional `.omr/locale.json` write; `--list` dumps timezone map |
| `version_control.py` | Workspace research tags and backups (`.omr/versions/`, `.omr/backups/`) |
| `skill_version.py` | Skill-package semver: `show` / `check` / `sync` / `set` / `bump` against `SKILL.md` (+ marketplace + `CHANGELOG.md`) |
| `collect_cli.py` | Optional: record a URL/query into `materials/` + index (creates only parent dirs of files written) |

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
Examples:

```bash
# 1. Author/refresh the presentation spec, then edit docs/<mode>/_document.json
python3 scripts/export_report.py --emit-spec --mode survey

# 2. Render, applying that spec
python3 scripts/export_report.py --mode survey --format docx --language en
python3 scripts/export_report.py --mode report --format pdf --language zh-CN
python3 scripts/version_control.py tag v1.0
python3 scripts/skill_version.py show
python3 scripts/skill_version.py check
python3 scripts/skill_version.py bump patch --message "Fix export edge case"
python3 scripts/collect_cli.py "https://arxiv.org/abs/…"
```

Skill package versioning (from **repo root**):

```bash
python3 skills/oh-my-research/scripts/skill_version.py bump minor --message "…"
```

`skill_version.py` manages the skill package only. Workspace research tags stay on `version_control.py`.

Long reports: the agent writes `.omr/report-state.json`, `docs/<mode>/chapters/`, and `docs/<mode>/_document.json` per `references/SYNTH/long-report.md`, then calls `export_report.py`. Presentation (fonts, cover, TOC, colors, chapter order) is decided in `_document.json`, not the script. Working `_*.md` files are not exported (`_document.json` is read but not rendered as content).

`export_report.py` refuses unsafe internal terminology at render time — fix prose and retry.

Python 3.10+ recommended.

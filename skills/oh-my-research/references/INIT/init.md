# INIT Mode

Initialize a **minimal** Oh-My-Research workspace. **LLM-driven** — create files directly (no init script). See `LLM-STATE.md`.

## Trigger

```
init "<topic>"
```

Also: new project, start research, initialize workspace, or first message with a research topic and no workspace.

## Hard rule: no empty folders

**Never** create a directory unless you are about to write at least one file into it in the same step.

- INIT creates only files that exist immediately (`AGENTS.md`, `.omr/tree-state.json`, `.omr/pattern.json`, `.omr/locale.json`). `<workspace>/.omr/` appears because those JSON files are written — not as an empty shell.
- Do **not** scaffold `materials/`, `docs/`, `docs/plans/`, `docs/index/`, `docs/ideas/`, `docs/survey|report|…/`, `chapters/`, `deliverables/`, `deliverables/wiki/`, `.omr/quality-gates/`, `.omr/versions/`, `.omr/backups/`, etc. `deliverables/` is the working-root public hand-off and appears only when the first export lands in it.
- Later modes create a path’s parent dirs **only when writing the first real artifact** there (e.g. first paper PDF → `<workspace>/materials/papers-raw/…`, first paper Markdown → `<workspace>/materials/papers/…`; first judgment → `<workspace>/docs/plans/…`).

## Existing topic first (mandatory)

`_omr/` is the default working root (container), not automatically the workspace for the new question.

1. If the user supplied `--workspace <path>`, use it as the active workspace and skip the scan.
2. Otherwise scan the working root for directories containing both `AGENTS.md` and `.omr/tree-state.json`; the root itself counts as a legacy single-topic workspace.
3. Match the new question against the topic slug and the `Research Question` / title in `AGENTS.md`, plus names in `deliverables/`. Exactly one match → **resume that workspace; do not INIT again**. Several matches → ask the user to pick. No match → continue with INIT below and create `<working-root>/<topic-slug>/`.
4. Record the resolved active workspace path; every later op and script call uses it.

## Steps

1. Derive `topic-slug` from the topic: lowercase, spaces → hyphens (e.g. `agent memory` → `agent-memory`). Use the user-supplied `--workspace` when present; otherwise create `<project-root>/_omr/<topic-slug>/` as the active workspace. A legacy single-topic workspace directly at `<project-root>/_omr/` is still valid when it already matches the question.
2. Create **only** (inside the active workspace):

```
<working-root>/<topic-slug>/   # active workspace; <working-root> defaults to <project-root>/_omr
├── AGENTS.md
└── .omr/
    ├── tree-state.json
    ├── pattern.json
    └── locale.json      # preferred language from timezone/locale (BCP-47 tag)
```

3. Fill `AGENTS.md` from `assets/templates/AGENTS.md.template` with this topic’s placeholders. Describe on-demand paths as documentation — do not mkdir them.
4. Write `.omr/tree-state.json` appropriate to the start (typically unlock collect/idea/think; lock synth until analysis). Adjust if the user starts mid-stream (e.g. materials already present).
5. Write `.omr/pattern.json` — default `{ "name": "Evidence-Deep" }` unless the user chose another pattern.
6. Detect preferred language from timezone/locale (`LANGUAGE.md` / `scripts/prefer_language.py --write-workspace <active-workspace>`; note that `--workspace` alone is read-only) and write `.omr/locale.json`. Mention it in the INIT reply; user can override.
7. Show next steps tailored to the topic.

## No coding dirs

Do not create `src/` or evaluation folders.

## Chat reply

`[INIT] Workspace: <active-workspace>. Topic: … Pattern: Evidence-Deep. Language: ja (timezone Asia/Tokyo). Next: collect <url|query>.`

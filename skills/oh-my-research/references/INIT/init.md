# INIT Mode

Initialize a **minimal** Oh-My-Research workspace. **LLM-driven** — create files directly (no init script). See `LLM-STATE.md`.

## Trigger

```
init "<topic>"
```

Also: new project, start research, initialize workspace, or first message with a research topic and no workspace.

## Hard rule: no empty folders

**Never** create a directory unless you are about to write at least one file into it in the same step.

- INIT creates only files that exist immediately (`AGENTS.md`, `.omr/tree-state.json`, `.omr/pattern.json`). `.omr/` appears because those JSON files are written — not as an empty shell.
- Do **not** scaffold `materials/`, `docs/`, `wiki/`, `docs/plans/`, `docs/index/`, `docs/ideas/`, `docs/survey|report|…/`, `chapters/`, `deliverables/`, `.omr/quality-gates/`, `.omr/versions/`, `.omr/backups/`, etc.
- Later modes create a path’s parent dirs **only when writing the first real artifact** there (e.g. first paper → `materials/papers/…`; first judgment → `docs/plans/…`).

## Steps

1. Derive `project-id`: lowercase, spaces → hyphens (e.g. `agent memory` → `agent-memory`). Adapt if the user wants an in-place workspace.
2. Create **only**:

```
<project-id>/   # or current dir if already the project root
├── AGENTS.md
└── .omr/
    ├── tree-state.json
    └── pattern.json
```

3. Fill `AGENTS.md` from `assets/templates/AGENTS.md.template` with this topic’s placeholders. Describe on-demand paths as documentation — do not mkdir them.
4. Write `.omr/tree-state.json` appropriate to the start (typically unlock collect/idea/think; lock synth until analysis). Adjust if the user starts mid-stream (e.g. materials already present).
5. Write `.omr/pattern.json` — default `{ "name": "Evidence-Deep" }` unless the user chose another pattern.
6. Show next steps tailored to the topic.

## No coding dirs

Do not create `src/` or evaluation folders.

## Chat reply

`[INIT] Project: … Pattern: Evidence-Deep. Next: collect <url|query>. Layout: files only until first content write.`

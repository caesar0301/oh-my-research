# INIT Mode

Initialize a minimal Oh-My-Research workspace. **LLM-driven** — create files directly (no init script). See `LLM-STATE.md`.

## Trigger

```
init "<topic>"
```

Also: new project, start research, initialize workspace, or first message with a research topic and no workspace.

## Steps

1. Derive `project-id`: lowercase, spaces → hyphens (e.g. `agent memory` → `agent-memory`). Adapt if the user wants an in-place workspace.
2. Create:

```
<project-id>/   # or current dir if already the project root
├── AGENTS.md
└── .omr/
    ├── tree-state.json
    └── pattern.json
```

3. Do **not** pre-create empty `materials/`, `docs/`, `wiki/` — create on first write.
4. Fill `AGENTS.md` from `assets/templates/AGENTS.md.template` with this topic’s placeholders.
5. Write `.omr/tree-state.json` appropriate to the start (typically unlock collect/idea/think; lock synth until analysis). Adjust if the user starts mid-stream (e.g. materials already present).
6. Write `.omr/pattern.json` — default `{ "name": "Evidence-Deep" }` unless the user chose another pattern.
7. Show next steps tailored to the topic.

## No coding dirs

Do not create `src/` or evaluation folders.

## Chat reply

`[INIT] Project: … Pattern: Evidence-Deep. Next: collect <url|query>.`

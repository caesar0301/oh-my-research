# INIT Mode

Initialize a minimal Oh-My-Research workspace.

## Trigger

```
init "<topic>"
```

Also: new project, start research, initialize workspace, or first message with a research topic and no workspace.

## Steps

1. Derive `project-id`: lowercase, spaces → hyphens (e.g. `agent memory` → `agent-memory`).
2. Create workspace in current directory (or ask if unclear):

```
<project-id>/   # or current dir if already the project root
├── AGENTS.md
└── .omr/
    ├── tree-state.json
    └── pattern.json          # default Evidence-Deep
```

3. Do **not** pre-create empty `materials/`, `docs/`, `wiki/` — create on first write.
4. Fill `AGENTS.md` from `assets/templates/AGENTS.md.template`.
5. Write tree-state:

```json
{
  "unlocked": ["init", "collect", "idea", "think"],
  "ready": [],
  "locked": ["analyze", "synth", "decide", "reconcile"],
  "completed": ["init"]
}
```

6. Copy default pattern name into `.omr/pattern.json` pointing at Evidence-Deep (inline or `"name": "Evidence-Deep"`).
7. Show next steps: `collect` sources or describe what to gather.

## No coding dirs

Do not create `src/` or evaluation folders.

## Chat reply

`[INIT] Project: … Pattern: Evidence-Deep. Next: collect <url|query>.`

# OMR Scripts

Helpers for the `oh-my-research` skill. Agents may run these; they are not a substitute for following `references/*.md`.

| Script | Purpose |
|--------|---------|
| `init_workspace.py` | Create `AGENTS.md` + `.omr/` |
| `collect_cli.py` | Index sources + placeholder material files |
| `tree_state.py` | Unlock / complete ops in `.omr/tree-state.json` |
| `loop_state.py` | Gate L loop state |
| `quality_gate.py` | QA1 / publication-safe QA2 heuristics → `.omr/quality-gates/*.json` |
| `version_control.py` | Tags and backups |
| `methods_registry.py` | THINK method offer/find from `assets/think/methods.csv` |
| `export_report.py` | Render publication-safe English/Chinese DOCX or PDF |

Install export dependencies:

```bash
python3 -m pip install -r scripts/requirements.txt
```

Examples:

```bash
python3 scripts/export_report.py --mode survey --format docx --language en
python3 scripts/export_report.py --mode report --format pdf --language zh-CN
```

The exporter refuses to publish chapters containing internal material IDs,
workflow/gate names, private artifact paths, or evidence-grade annotations.
Fix the reader-facing citations and prose, then export again.

No evaluation / prototype runners are included. Python 3.10+ recommended.

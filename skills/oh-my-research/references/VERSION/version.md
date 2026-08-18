# VERSION Mode

Lightweight version management for research workspaces.

## Trigger

```
version tag <label>
version history
version diff <a> <b>
version backup
version list
```

## Behavior

| Command | Action |
|---------|--------|
| `tag` | Record label + timestamp + artifact hashes/paths under `.omr/versions/` |
| `history` | List tags chronologically |
| `diff` | Summarize file-level changes between two tags/backups |
| `backup` | Timestamped copy of `docs/plans` + current synth mode dirs (+ optional wiki) into `docs/archive/` or `.omr/backups/` |
| `list` | List backups and tags |

Script: `scripts/version_control.py`

## Practice

Tag after Gate A pass and after Gate D publish.

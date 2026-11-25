#!/usr/bin/env python3
"""Resolve the OMR working root (container).

The working root is the directory that holds topic workspaces (or, for a
single-topic project, the workspace itself). The default is the hidden
``.omr/`` directory. This module keeps a single, shared resolution rule so
every mechanical script agrees on the root.

Precedence (highest first):

  1. an explicit ``--workspace`` path (callers handle this verbatim),
  2. the ``OMR_WORKSPACE_ROOT`` environment variable,
  3. ``<cwd>/.omr`` (created later by INIT when it does not exist yet).

Note: the per-workspace state directory is also named ``.omr`` (e.g.
``<workspace>/.omr/tree-state.json``). That is a different level — it lives
*inside* the active workspace, not at the project root — so the two uses do
not collide.
"""

from __future__ import annotations

import os
from pathlib import Path

PREFERRED_DIRNAME = ".omr"
ENV_VAR = "OMR_WORKSPACE_ROOT"

# Shared argparse help text so every script advertises the same default.
DEFAULT_HELP = "<cwd>/.omr"


def resolve_workspace_root(
    workspace: str | Path | None = None,
    *,
    base: Path | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    """Return the resolved working root as an absolute :class:`Path`.

    Parameters
    ----------
    workspace:
        An explicit override (e.g. ``--workspace``). When given it always wins
        and is returned verbatim (resolved to an absolute path).
    base:
        Directory to look in for ``.omr``. Defaults to ``Path.cwd()``.
        Mostly useful for tests.
    env:
        Environment mapping to read ``OMR_WORKSPACE_ROOT`` from. Defaults to
        ``os.environ``. Mostly useful for tests.
    """
    if workspace is not None:
        return Path(workspace).resolve()

    environ = env if env is not None else os.environ
    override = environ.get(ENV_VAR)
    if override:
        return Path(override).resolve()

    root = (base or Path.cwd()).resolve()
    return root / PREFERRED_DIRNAME


if __name__ == "__main__":
    # Handy for agents/scripts that need to know the resolved root without
    # importing Python: `python3 scripts/workspace_root.py`.
    print(resolve_workspace_root())

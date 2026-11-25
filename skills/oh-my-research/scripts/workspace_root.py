#!/usr/bin/env python3
"""Resolve the OMR working root (container) with legacy compatibility.

The working root is the directory that holds topic workspaces (or, for a
legacy single-topic project, the workspace itself). The modern default is the
hidden ``.omr/`` directory; older projects used ``_omr/``. This module keeps a
single, shared resolution rule so every mechanical script agrees on the root.

Precedence (highest first):

  1. an explicit ``--workspace`` path (callers handle this verbatim),
  2. the ``OMR_WORKSPACE_ROOT`` environment variable,
  3. an existing ``<cwd>/.omr`` directory          (modern default),
  4. an existing ``<cwd>/_omr`` directory          (legacy fallback),
  5. ``<cwd>/.omr``                                (modern default, created
     later by INIT when it does not exist yet).

Rule 4 is the compatibility guarantee: a project that already has ``_omr/``
keeps using it instead of silently abandoning its data in a fresh ``.omr/``.
Rule 5 means brand-new projects get ``.omr`` without any migration step.

Note: the per-workspace state directory is also named ``.omr`` (e.g.
``<workspace>/.omr/tree-state.json``). That is a different level — it lives
*inside* the active workspace, not at the project root — so the two uses do
not collide.
"""

from __future__ import annotations

import os
from pathlib import Path

PREFERRED_DIRNAME = ".omr"
LEGACY_DIRNAME = "_omr"
ENV_VAR = "OMR_WORKSPACE_ROOT"

# Shared argparse help text so every script advertises the same default.
DEFAULT_HELP = "<cwd>/.omr (legacy <cwd>/_omr)"


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
        Directory to look in for ``.omr`` / ``_omr``. Defaults to ``Path.cwd()``.
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
    preferred = root / PREFERRED_DIRNAME
    legacy = root / LEGACY_DIRNAME

    if preferred.is_dir():
        return preferred
    if legacy.is_dir():
        return legacy
    return preferred


if __name__ == "__main__":
    # Handy for agents/scripts that need to know the resolved root without
    # importing Python: `python3 scripts/workspace_root.py`.
    print(resolve_workspace_root())

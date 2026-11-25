"""Tests for the shared OMR working-root resolver.

Verifies the `.omr` default, the legacy `_omr` fallback, the "both exist"
precedence, explicit overrides, and the ``OMR_WORKSPACE_ROOT`` env var.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "skills/oh-my-research/scripts"),
)

import workspace_root  # noqa: E402


class WorkspaceRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        # macOS: /var is a symlink to /private/var; resolve() in the resolver
        # returns the canonical path, so normalize the base for comparisons.
        self.base = Path(self.tmp.name).resolve()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def resolve(self, *, env: dict[str, str] | None = None):
        return workspace_root.resolve_workspace_root(base=self.base, env=env or {})

    def test_prefers_dot_omr_when_nothing_exists(self) -> None:
        # Brand-new project: default to the hidden .omr container.
        self.assertEqual(self.resolve(), self.base / ".omr")

    def test_falls_back_to_legacy_omr_when_only_that_exists(self) -> None:
        (self.base / "_omr").mkdir()
        self.assertEqual(self.resolve(), self.base / "_omr")

    def test_dot_omr_wins_when_both_exist(self) -> None:
        (self.base / ".omr").mkdir()
        (self.base / "_omr").mkdir()
        self.assertEqual(self.resolve(), self.base / ".omr")

    def test_explicit_workspace_always_wins(self) -> None:
        (self.base / ".omr").mkdir()
        (self.base / "_omr").mkdir()
        explicit = self.base / "custom-root"
        self.assertEqual(
            workspace_root.resolve_workspace_root(explicit, base=self.base, env={}),
            explicit.resolve(),
        )

    def test_env_var_overrides_cwd_lookup(self) -> None:
        (self.base / ".omr").mkdir()
        override = self.base / "env-root"
        self.assertEqual(
            self.resolve(env={"OMR_WORKSPACE_ROOT": str(override)}),
            override.resolve(),
        )

    def test_explicit_workspace_beats_env_var(self) -> None:
        explicit = self.base / "explicit"
        self.assertEqual(
            workspace_root.resolve_workspace_root(
                explicit,
                base=self.base,
                env={"OMR_WORKSPACE_ROOT": str(self.base / "env-root")},
            ),
            explicit.resolve(),
        )

    def test_constants(self) -> None:
        self.assertEqual(workspace_root.PREFERRED_DIRNAME, ".omr")
        self.assertEqual(workspace_root.LEGACY_DIRNAME, "_omr")
        self.assertEqual(workspace_root.ENV_VAR, "OMR_WORKSPACE_ROOT")


if __name__ == "__main__":
    unittest.main()

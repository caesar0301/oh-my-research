"""Tests for the structural skill-package Markdown lint."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import skill_lint  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_SKILL_ROOT = REPO_ROOT / "skills/oh-my-research"


def make_skill(root: Path) -> None:
    """Minimal clean fixture: one indexed doc + index + scripts catalog."""
    (root / "references").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "SKILL.md").write_text(
        "---\n"
        "name: test-skill\n"
        "description: Processes test fixtures when a test request arrives.\n"
        "---\n\n"
        "# Test Skill\n\n"
        "See `references/a.md`.\n",
        encoding="utf-8",
    )
    (root / "references/a.md").write_text(
        "# A\n\n> Load when: testing A. Depth: lean.\n\n## One\n\ntext\n",
        encoding="utf-8",
    )
    (root / "scripts/README.md").write_text(
        "# Scripts\n\n> Load when: invoking scripts. Depth: lean.\n\n## Table\n\ntext\n",
        encoding="utf-8",
    )
    (root / "references/REFERENCE.md").write_text(
        "# Index\n\n> Load when: locating docs. Depth: lean.\n\n## File Index\n\n"
        "| File | Role | Keywords |\n|------|------|----------|\n"
        "| `references/REFERENCE.md` | This file | index |\n"
        "| `references/a.md` | A doc | a |\n"
        "| `scripts/README.md` | Scripts | scripts |\n",
        encoding="utf-8",
    )


def rules_of(report: dict) -> set[tuple[str, str]]:
    return {(issue["file"], issue["rule"]) for issue in report["issues"]}


class SkillLintRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "skill"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def report(self) -> dict:
        return skill_lint.run(self.root)

    def test_clean_fixture_passes(self) -> None:
        make_skill(self.root)
        report = self.report()
        self.assertEqual(report["issues"], [])
        self.assertTrue(report["ok"])

    def test_skill_line_budget(self) -> None:
        make_skill(self.root)
        (self.root / "SKILL.md").write_text(
            "# Test Skill\n\n" + "filler\n" * 600, encoding="utf-8"
        )
        self.assertIn(("SKILL.md", "skill_line_budget"), rules_of(self.report()))

    def test_description_missing(self) -> None:
        make_skill(self.root)
        (self.root / "SKILL.md").write_text("# Test Skill\n\ntext\n", encoding="utf-8")
        self.assertIn(("SKILL.md", "description_present"), rules_of(self.report()))

    def test_description_too_long(self) -> None:
        make_skill(self.root)
        (self.root / "SKILL.md").write_text(
            "---\ndescription: "
            + "x" * 1100
            + "\n---\n\n# Test Skill\n\nSee `references/a.md`.\n",
            encoding="utf-8",
        )
        self.assertIn(("SKILL.md", "description_length"), rules_of(self.report()))

    def test_skill_reference_must_exist(self) -> None:
        make_skill(self.root)
        (self.root / "SKILL.md").write_text(
            "---\ndescription: d\n---\n\n# Test Skill\n\nSee `references/ghost.md`.\n",
            encoding="utf-8",
        )
        self.assertIn(("SKILL.md", "skill_ref_exists"), rules_of(self.report()))

    def test_missing_h1_and_duplicate_h1(self) -> None:
        make_skill(self.root)
        (self.root / "references/a.md").write_text(
            "no heading\n\n> Load when: testing A. Depth: lean.\n\ntext\n",
            encoding="utf-8",
        )
        self.assertIn(("references/a.md", "single_h1"), rules_of(self.report()))
        (self.root / "references/a.md").write_text(
            "# A\n\n> Load when: testing A. Depth: lean.\n\n# Again\n\ntext\n",
            encoding="utf-8",
        )
        self.assertIn(("references/a.md", "single_h1"), rules_of(self.report()))

    def test_h1_must_be_first_line(self) -> None:
        make_skill(self.root)
        (self.root / "references/a.md").write_text(
            "preamble\n\n# A\n\n> Load when: testing A. Depth: lean.\n\ntext\n",
            encoding="utf-8",
        )
        self.assertIn(("references/a.md", "h1_first_line"), rules_of(self.report()))

    def test_heading_level_skip(self) -> None:
        make_skill(self.root)
        (self.root / "references/a.md").write_text(
            "# A\n\n> Load when: testing A. Depth: lean.\n\n### Skipped\n\ntext\n",
            encoding="utf-8",
        )
        self.assertIn(("references/a.md", "heading_no_skip"), rules_of(self.report()))

    def test_load_when_required(self) -> None:
        make_skill(self.root)
        (self.root / "references/a.md").write_text(
            "# A\n\n## One\n\ntext\n", encoding="utf-8"
        )
        self.assertIn(("references/a.md", "load_when_present"), rules_of(self.report()))

    def test_long_doc_requires_toc(self) -> None:
        make_skill(self.root)
        (self.root / "references/long.md").write_text(
            "# Long\n\n> Load when: testing. Depth: deep.\n\n## One\n\n"
            + "text\n" * 110
            + "\n| `references/long.md` | Long doc | long |\n",
            encoding="utf-8",
        )
        issues = rules_of(self.report())
        self.assertIn(("references/long.md", "toc_present"), issues)
        (self.root / "references/long.md").write_text(
            "# Long\n\n> Load when: testing. Depth: deep.\n\n## Contents\n\n- [One](#one)\n\n## One\n\n"
            + "text\n" * 110,
            encoding="utf-8",
        )
        issues = rules_of(self.report())
        self.assertNotIn(("references/long.md", "toc_present"), issues)

    def test_short_doc_needs_no_toc(self) -> None:
        make_skill(self.root)
        (self.root / "references/short.md").write_text(
            "# Short\n\n> Load when: testing. Depth: lean.\n\ntext\n", encoding="utf-8"
        )
        # Not indexed → orphan; but no toc_present rule for ≤100-line docs.
        issues = rules_of(self.report())
        self.assertNotIn(("references/short.md", "toc_present"), issues)

    def test_orphan_doc_not_indexed(self) -> None:
        make_skill(self.root)
        (self.root / "references/orphan.md").write_text(
            "# Orphan\n\n> Load when: never. Depth: lean.\n\ntext\n", encoding="utf-8"
        )
        self.assertIn(
            ("references/orphan.md", "indexed_in_reference"), rules_of(self.report())
        )

    def test_method_playbook_indexed_by_filename(self) -> None:
        make_skill(self.root)
        method_dir = self.root / "references/THINK/methods"
        method_dir.mkdir(parents=True)
        (method_dir / "first-principles.md").write_text(
            "# First Principles\n\n> Load when: running the method. Depth: deep.\n\ntext\n",
            encoding="utf-8",
        )
        index = self.root / "references/REFERENCE.md"
        index.write_text(
            index.read_text(encoding="utf-8")
            + "\n| `first-principles.md` | Rebuild from truths | deep |\n",
            encoding="utf-8",
        )
        self.assertNotIn(
            ("references/THINK/methods/first-principles.md", "indexed_in_reference"),
            rules_of(self.report()),
        )

    def test_fenced_code_headings_ignored(self) -> None:
        make_skill(self.root)
        (self.root / "references/a.md").write_text(
            "# A\n\n"
            "> Load when: testing A. Depth: lean.\n\n"
            "## One\n\n"
            "```markdown\n"
            "# Not a heading\n\n"
            "### Not a skip\n\n"
            "> Load when: not counted twice\n"
            "```\n\n"
            "text\n",
            encoding="utf-8",
        )
        report = self.report()
        self.assertNotIn(("references/a.md", "single_h1"), rules_of(report))
        self.assertNotIn(("references/a.md", "heading_no_skip"), rules_of(report))


class SkillLintCliTests(unittest.TestCase):
    def test_exit_code_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            make_skill(root)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = skill_lint.main(["--root", str(root), "--json"])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(buffer.getvalue())["ok"])

    def test_real_repo_tree_is_clean(self) -> None:
        report = skill_lint.run(REAL_SKILL_ROOT)
        self.assertEqual(report["issues"], [], report["issues"])


if __name__ == "__main__":
    unittest.main()

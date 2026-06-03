#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Tests for scripts/validate_skill_names.py.

Run directly: `uv run --script tests/test_validate_skill_names.py`.
"""
import importlib.util
import pathlib
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_skill_names.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_skill_names", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALID_FRONTMATTER = """\
---
name: {name}
description: A valid description that explains what the skill does and when.
---

# Body
"""


class ValidateSkillNamesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_validator()

    def _skill(self, root: pathlib.Path, name: str, body: str, filename="SKILL.md"):
        skill_dir = root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / filename).write_text(body)
        return skill_dir

    def evaluate(self, name: str, body: str, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._skill(pathlib.Path(tmp), name, body, **kwargs)
            return self.mod.evaluate_skill(skill_dir)

    def test_valid_skill_passes(self):
        result = self.evaluate(
            "good-skill", VALID_FRONTMATTER.format(name="good-skill")
        )
        self.assertTrue(result["ok"], result["issues"])
        self.assertEqual(result["name"], "good-skill")

    def test_lowercase_skill_md_accepted(self):
        result = self.evaluate(
            "good-skill",
            VALID_FRONTMATTER.format(name="good-skill"),
            filename="skill.md",
        )
        self.assertTrue(result["ok"], result["issues"])

    def test_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = pathlib.Path(tmp) / "empty"
            skill_dir.mkdir()
            result = self.mod.evaluate_skill(skill_dir)
        self.assertFalse(result["ok"])
        self.assertTrue(any("missing SKILL.md" in i for i in result["issues"]))

    def test_name_must_match_directory(self):
        result = self.evaluate(
            "dir-name", VALID_FRONTMATTER.format(name="other-name")
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any("must equal the skill directory" in i for i in result["issues"]))

    def test_uppercase_name_rejected(self):
        result = self.evaluate("BadName", VALID_FRONTMATTER.format(name="BadName"))
        self.assertFalse(result["ok"])

    def test_consecutive_hyphens_rejected(self):
        result = self.evaluate(
            "bad--name", VALID_FRONTMATTER.format(name="bad--name")
        )
        self.assertFalse(result["ok"])

    def test_name_too_long_rejected(self):
        long = "a" * 65
        result = self.evaluate(long, VALID_FRONTMATTER.format(name=long))
        self.assertFalse(result["ok"])
        self.assertTrue(any("exceeds" in i for i in result["issues"]))

    def test_missing_description_rejected(self):
        body = "---\nname: no-desc\n---\n# Body\n"
        result = self.evaluate("no-desc", body)
        self.assertFalse(result["ok"])
        self.assertTrue(any("description" in i for i in result["issues"]))

    def test_empty_description_rejected(self):
        body = "---\nname: blank-desc\ndescription: '   '\n---\n# Body\n"
        result = self.evaluate("blank-desc", body)
        self.assertFalse(result["ok"])

    def test_description_too_long_rejected(self):
        desc = "x" * 1025
        body = f"---\nname: long-desc\ndescription: {desc}\n---\n# Body\n"
        result = self.evaluate("long-desc", body)
        self.assertFalse(result["ok"])
        self.assertTrue(any("1024" in i for i in result["issues"]))

    def test_unexpected_field_rejected(self):
        body = (
            "---\nname: extra-field\n"
            "description: A valid description here.\n"
            "bogus: nope\n---\n# Body\n"
        )
        result = self.evaluate("extra-field", body)
        self.assertFalse(result["ok"])
        self.assertTrue(any("unexpected frontmatter" in i for i in result["issues"]))

    def test_compatibility_too_long_rejected(self):
        compat = "c" * 501
        body = (
            "---\nname: compat-skill\n"
            "description: A valid description here.\n"
            f"compatibility: {compat}\n---\n# Body\n"
        )
        result = self.evaluate("compat-skill", body)
        self.assertFalse(result["ok"])
        self.assertTrue(any("compatibility exceeds" in i for i in result["issues"]))

    def test_allowed_optional_fields_accepted(self):
        body = (
            "---\nname: full-skill\n"
            "description: A valid description here.\n"
            "license: Apache-2.0\n"
            "allowed-tools: Bash Read Write\n"
            "compatibility: Requires uv and git.\n"
            "metadata:\n  version: \"1.0\"\n---\n# Body\n"
        )
        result = self.evaluate("full-skill", body)
        self.assertTrue(result["ok"], result["issues"])

    def test_missing_frontmatter_rejected(self):
        result = self.evaluate("no-front", "# Just a body\n")
        self.assertFalse(result["ok"])

    def test_invalid_yaml_rejected(self):
        body = "---\nname: bad-yaml\ndescription: [unclosed\n---\n# Body\n"
        result = self.evaluate("bad-yaml", body)
        self.assertFalse(result["ok"])

    def test_real_repository_skills_pass(self):
        skills_root = REPO_ROOT / "skills"
        skills = self.mod.discover_skills(skills_root)
        self.assertTrue(skills, "expected at least one skill in skills/")
        for skill_dir in skills:
            result = self.mod.evaluate_skill(skill_dir)
            self.assertTrue(result["ok"], f"{skill_dir.name}: {result['issues']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

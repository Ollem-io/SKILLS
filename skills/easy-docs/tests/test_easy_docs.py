#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "easy_docs.py"
PYPROJECT_PATH = SKILL_ROOT / "pyproject.toml"
SKILL_MD_PATH = SKILL_ROOT / "SKILL.md"
UV = shutil.which("uv") or "uv"


def load_easy_docs():
    spec = importlib.util.spec_from_file_location("easy_docs", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def concept(
    concept_type: str,
    title: str,
    description: str,
    body: str = "Content.",
) -> str:
    return (
        "---\n"
        f"type: {concept_type}\n"
        f"title: {title}\n"
        f"description: {description}\n"
        "timestamp: 1970-01-01\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )


class EasyDocsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_docs = load_easy_docs()

    def run_script(
        self,
        root: pathlib.Path,
        command: str,
        *args: str,
        expected_status: int = 0,
    ) -> tuple[dict, str]:
        result = subprocess.run(
            [
                UV,
                "run",
                "--script",
                str(SCRIPT_PATH),
                command,
                "--root",
                str(root),
                *args,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(
            result.returncode,
            expected_status,
            f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}",
        )
        parsed = json.loads(result.stdout)
        self.assertEqual(
            result.stdout, json.dumps(parsed, indent=2, sort_keys=True) + "\n"
        )
        return parsed, result.stdout

    def tree_hash(self, root: pathlib.Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(root.rglob("*")):
            if not path.is_file() or ".git" in path.parts:
                continue
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def scaffold_and_index(self, root: pathlib.Path) -> None:
        self.run_script(root, "scaffold")
        self.run_script(root, "index", "--write")

    def test_scaffold_creates_full_tree_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first, _ = self.run_script(root, "scaffold")

            self.assertEqual(first["bundle"], "docs")
            self.assertEqual(len(first["created"]), 20)
            self.assertEqual(first["existing"], [])
            expected = {
                "docs/index.md",
                "docs/architecture.md",
                "docs/repo-standards.md",
                "docs/local-development.md",
                "docs/testing.md",
                "docs/validation-loop.md",
                "docs/observability.md",
                "docs/security.md",
                "docs/reliability.md",
                "docs/release-process.md",
                "docs/pr-review-workflow.md",
                "docs/merge-policy.md",
                "docs/cleanup-workflow.md",
                "docs/engineering-maintenance.md",
                "docs/decisions/index.md",
                "docs/design/index.md",
                "docs/exec-plans/index.md",
                "docs/references/index.md",
                "docs/references/docs-maintenance.md",
                "docs/references/entrypoint-readme-template.md",
            }
            self.assertEqual(set(first["created"]), expected)
            self.assertIn('okf_version: "0.1"', (root / "docs/index.md").read_text())
            self.assertNotIn("---", (root / "docs/decisions/index.md").read_text())
            self.assertIn(
                "## Definition of Done",
                (root / "docs/references/entrypoint-readme-template.md").read_text(),
            )

            before = self.tree_hash(root)
            second, _ = self.run_script(root, "scaffold")
            self.assertEqual(self.tree_hash(root), before)
            self.assertEqual(second["created"], [])
            self.assertEqual(second["existing"], sorted(expected))

    def test_scaffold_never_overwrites_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            custom = root / "docs/architecture.md"
            custom.parent.mkdir(parents=True)
            custom.write_text("custom architecture\n")

            result, _ = self.run_script(root, "scaffold")

            self.assertEqual(custom.read_text(), "custom architecture\n")
            self.assertIn("docs/architecture.md", result["existing"])
            self.assertNotIn("docs/architecture.md", result["created"])

    def test_headers_derive_values_preserve_existing_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            (docs / "decisions").mkdir(parents=True)
            (docs / "references").mkdir()
            decision = docs / "decisions/0001-cache.md"
            reference = docs / "references/tooling.md"
            guide = docs / "local-development.md"
            decision.write_text("# Cache Strategy\n\nUse a bounded local cache.\n")
            reference.write_text("Reference material starts here.\n")
            guide.write_text("# Local Workflow\n\nInstall dependencies first.\n")
            existing = docs / "existing.md"
            existing_content = "---\ntype: Custom\nextra: keep-me\n---\n\nExisting.\n"
            existing.write_text(existing_content)

            before = self.tree_hash(root)
            checked, _ = self.run_script(root, "headers", "--check", expected_status=1)
            self.assertEqual(self.tree_hash(root), before)
            self.assertEqual(
                checked["missing"],
                [
                    "docs/decisions/0001-cache.md",
                    "docs/local-development.md",
                    "docs/references/tooling.md",
                ],
            )

            written, _ = self.run_script(
                root, "headers", "--write", "--default-date", "2026-07-15"
            )
            self.assertEqual(written["written"], checked["missing"])
            self.assertEqual(existing.read_text(), existing_content)
            decision_text = decision.read_text()
            self.assertIn("type: Decision Record", decision_text)
            self.assertIn("title: Cache Strategy", decision_text)
            self.assertIn("description: Use a bounded local cache.", decision_text)
            self.assertIn("timestamp: '2026-07-15'", decision_text)
            self.assertIn("type: Reference", reference.read_text())
            self.assertIn("title: Tooling", reference.read_text())
            self.assertIn("type: Guide", guide.read_text())

            stable = self.tree_hash(root)
            second, _ = self.run_script(root, "headers", "--write")
            self.assertEqual(second["written"], [])
            self.assertEqual(self.tree_hash(root), stable)

    def test_headers_reject_broken_frontmatter_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "docs/broken.md"
            path.parent.mkdir(parents=True)
            original = "---\ntype: [\n# Broken\n"
            path.write_text(original)

            result, _ = self.run_script(root, "headers", "--write", expected_status=1)

            self.assertEqual(result["invalid"], ["docs/broken.md"])
            self.assertEqual(result["written"], [])
            self.assertEqual(path.read_text(), original)

    def test_index_writes_grouped_sorted_catalog_and_preserves_surrounding_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            decisions = docs / "decisions"
            manual = docs / "manual"
            decisions.mkdir(parents=True)
            manual.mkdir()
            root_index = docs / "index.md"
            root_index.write_text(
                "# Hand Introduction\n\nBefore.\n\n"
                f"{self.easy_docs.GENERATED_INDEX_BEGIN}\nold\n"
                f"{self.easy_docs.GENERATED_INDEX_END}\n\nAfter.\n"
            )
            (docs / "zebra.md").write_text(
                concept("Guide", "Zebra", "Last alphabetically.")
            )
            (docs / "alpha.md").write_text(
                concept("Guide", "alpha", "First alphabetically.")
            )
            (docs / "reference.md").write_text(
                concept("Reference", "Reference", "Reference entry.")
            )
            (decisions / "index.md").write_text(
                "# Decisions\n\n"
                f"{self.easy_docs.GENERATED_INDEX_BEGIN}\n"
                f"{self.easy_docs.GENERATED_INDEX_END}\n"
            )
            (decisions / "0001-choice.md").write_text(
                concept("Decision Record", "Choice", "Choose one.")
            )
            unmanaged = manual / "index.md"
            unmanaged.write_text("# Hand Maintained\n\nDo not touch.\n")
            unmanaged_original = unmanaged.read_text()

            before = self.tree_hash(root)
            drifted, _ = self.run_script(root, "index", "--check", expected_status=1)
            self.assertEqual(self.tree_hash(root), before)
            self.assertEqual(
                drifted["drifted"],
                ["docs/decisions/index.md", "docs/index.md"],
            )
            self.assertEqual(drifted["unmanaged"], ["docs/manual/index.md"])

            result, _ = self.run_script(root, "index", "--write")
            self.assertEqual(result["written"], drifted["drifted"])
            generated = root_index.read_text()
            self.assertTrue(generated.startswith("# Hand Introduction\n\nBefore."))
            self.assertTrue(generated.endswith("\n\nAfter.\n"))
            self.assertLess(generated.index("[alpha]"), generated.index("[Zebra]"))
            self.assertLess(
                generated.index("## Guide"), generated.index("## Reference")
            )
            self.assertLess(
                generated.index("## Reference"), generated.index("## Sections")
            )
            self.assertIn("* [decisions/](decisions/)", generated)
            self.assertEqual(unmanaged.read_text(), unmanaged_original)

            clean, _ = self.run_script(root, "index", "--check")
            self.assertEqual(clean["drifted"], [])

    def test_index_updates_agents_region_only_when_markers_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "index.md").write_text(
                f"{self.easy_docs.GENERATED_INDEX_BEGIN}\n"
                f"{self.easy_docs.GENERATED_INDEX_END}\n"
            )
            (docs / "architecture.md").write_text(
                concept("Guide", "Architecture", "System map.")
            )
            agents = root / "AGENTS.md"
            agents.write_text(
                "# Agents\n\nKeep.\n\n"
                f"{self.easy_docs.GENERATED_CORE_BEGIN}\nstale\n"
                f"{self.easy_docs.GENERATED_CORE_END}\n\nTail.\n"
            )

            result, _ = self.run_script(root, "index", "--write")
            self.assertIn("AGENTS.md", result["written"])
            self.assertIn(
                "* [Architecture](docs/architecture.md) - System map.",
                agents.read_text(),
            )
            self.assertTrue(agents.read_text().endswith("\n\nTail.\n"))

            agents.write_text("# Agents\n\nHand maintained.\n")
            unchanged = agents.read_text()
            self.run_script(root, "index", "--write")
            self.assertEqual(agents.read_text(), unchanged)

    def test_check_passes_fresh_bundle_and_broken_link_is_warning_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)

            result, _ = self.run_script(root, "check")
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["warnings"], [])

            linked = root / "docs/linked.md"
            linked.write_text(
                concept("Guide", "Linked", "Link example.", "See [missing](nope.md).")
            )
            self.run_script(root, "index", "--write")
            warned, _ = self.run_script(root, "check")
            broken = [
                item for item in warned["warnings"] if item["code"] == "broken_link"
            ]
            self.assertEqual(len(broken), 1)
            self.assertEqual(broken[0]["path"], "docs/linked.md")

    def test_check_reports_required_error_classes(self):
        cases = {
            "missing_type": (
                "docs/no-type.md",
                "---\ntitle: No Type\ndescription: Missing type.\n---\n\n# No Type\n",
                "missing_type",
            ),
            "long_root": (
                "docs/long.md",
                concept("Guide", "Long", "Too long.", "\n".join(["line"] * 501)),
                "root_doc_too_long",
            ),
            "bad_log": (
                "docs/log.md",
                "# Log\n\n## yesterday\n\nChanged.\n",
                "invalid_log_heading",
            ),
            "missing_subdir_index": (
                "docs/topic/detail.md",
                concept("Guide", "Detail", "Nested detail."),
                "missing_index",
            ),
        }
        for name, (relative, content, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                self.scaffold_and_index(root)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                self.run_script(root, "index", "--write")

                result, _ = self.run_script(root, "check", expected_status=1)
                codes = {item["code"] for item in result["errors"]}
                self.assertIn(expected_code, codes)

    def test_check_modes_do_not_modify_tree_and_scans_skip_ignored_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            ignored = root / "docs/node_modules/package.md"
            hidden = root / "docs/.private/secret.md"
            ignored.parent.mkdir(parents=True)
            hidden.parent.mkdir(parents=True)
            ignored.write_text("missing frontmatter\n")
            hidden.write_text("missing frontmatter\n")

            baseline = self.tree_hash(root)
            for command, args in [
                ("headers", ("--check",)),
                ("index", ("--check",)),
                ("check", ()),
            ]:
                with self.subTest(command=command):
                    self.run_script(root, command, *args)
                    self.assertEqual(self.tree_hash(root), baseline)

    @unittest.skipUnless(
        shutil.which("git"), "git is required for timestamp derivation"
    )
    def test_headers_use_last_git_commit_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root / "docs/committed.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Committed\n\nCommitted prose.\n")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            environment = {
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
                "GIT_AUTHOR_DATE": "2024-02-03T12:00:00Z",
                "GIT_COMMITTER_DATE": "2024-02-03T12:00:00Z",
            }
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "test"],
                check=True,
                env={**os.environ, **environment},
            )

            self.run_script(root, "headers", "--write")

            self.assertIn("timestamp: '2024-02-03'", path.read_text())

    @unittest.skipUnless(os.name == "posix", "symlink tests require POSIX")
    def test_symlinked_markdown_is_never_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "repo"
            docs = root / "docs"
            docs.mkdir(parents=True)
            outside = pathlib.Path(tmp) / "outside.md"
            original = "# Outside\n\nDo not modify.\n"
            outside.write_text(original)
            (docs / "evil.md").symlink_to(outside)

            result, _ = self.run_script(root, "headers", "--write")

            self.assertEqual(result["written"], [])
            self.assertEqual(outside.read_text(), original)

            broken_target = pathlib.Path(tmp) / "missing-architecture.md"
            (docs / "architecture.md").symlink_to(broken_target)
            scaffolded, _ = self.run_script(root, "scaffold")

            self.assertIn("docs/architecture.md", scaffolded["existing"])
            self.assertFalse(broken_target.exists())

    def test_nonexistent_roots_and_bundles_fail_without_creating_directories(self):
        commands = (("headers", "--check"), ("index", "--check"), ("check",))
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            for command in commands:
                with self.subTest(command=command, missing="root"):
                    root = base / f"missing-{command[0]}"
                    result, _ = self.run_script(root, *command, expected_status=2)
                    self.assertEqual(
                        result, {"error": f"root not found: {root.resolve()}"}
                    )
                    self.assertFalse(root.exists())

                with self.subTest(command=command, missing="bundle"):
                    root = base / f"existing-{command[0]}"
                    root.mkdir()
                    result, _ = self.run_script(root, *command, expected_status=2)
                    self.assertEqual(result, {"error": "bundle not found: docs"})
                    self.assertFalse((root / "docs").exists())

    def test_check_rejects_non_string_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            (root / "docs/numeric-type.md").write_text(
                "---\ntype: 123\ntitle: Numeric\ndescription: Invalid type.\n---\n\n"
                "# Numeric\n"
            )
            self.run_script(root, "index", "--write")

            result, _ = self.run_script(root, "check", expected_status=1)

            errors = [
                item
                for item in result["errors"]
                if item["path"] == "docs/numeric-type.md"
            ]
            self.assertEqual([item["code"] for item in errors], ["invalid_type"])

    def test_only_bundle_root_index_may_have_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            nested = root / "docs/decisions/index.md"
            nested.write_text(
                "---\ntype: Guide\ntitle: Decisions\n---\n\n# Decisions\n\n"
                f"{self.easy_docs.GENERATED_INDEX_BEGIN}\n"
                f"{self.easy_docs.GENERATED_INDEX_END}\n"
            )
            self.run_script(root, "index", "--write")

            result, _ = self.run_script(root, "check", expected_status=1)

            index_errors = [
                item for item in result["errors"] if item["code"] == "index_frontmatter"
            ]
            self.assertEqual(
                [item["path"] for item in index_errors],
                ["docs/decisions/index.md"],
            )

    def test_malformed_index_and_agents_markers_fail_index_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            (root / "docs/index.md").write_text(
                f"# Documentation\n\n{self.easy_docs.GENERATED_INDEX_BEGIN}\n"
            )
            (root / "AGENTS.md").write_text(
                f"# Agents\n\n{self.easy_docs.GENERATED_CORE_BEGIN}\n"
            )

            indexed, _ = self.run_script(root, "index", "--check", expected_status=1)
            checked, _ = self.run_script(root, "check", expected_status=1)

            self.assertEqual(indexed["malformed"], ["AGENTS.md", "docs/index.md"])
            malformed_errors = [
                item
                for item in checked["errors"]
                if item["code"] == "malformed_markers"
            ]
            self.assertEqual(
                [item["path"] for item in malformed_errors],
                ["AGENTS.md", "docs/index.md"],
            )

    def test_log_dates_must_be_real_and_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            log = root / "docs/log.md"
            log.write_text("# Log\n\n## 2026-13-99\n\nChanged.\n")

            invalid, _ = self.run_script(root, "check", expected_status=1)

            self.assertIn(
                "invalid_log_heading",
                {item["code"] for item in invalid["errors"]},
            )

            log.write_text(
                "# Log\n\n## 2026-01-01\n\nOlder.\n\n## 2026-02-01\n\nNewer.\n"
            )
            ordered, _ = self.run_script(root, "check")
            self.assertIn("log_order", {item["code"] for item in ordered["warnings"]})

    def test_reserved_filenames_are_case_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True)
            (docs / "INDEX.md").write_text("# Uppercase Index\n")

            result, _ = self.run_script(root, "headers", "--check", expected_status=1)

            self.assertEqual(result["missing"], ["docs/INDEX.md"])

    def test_check_surfaces_ignored_directories_and_empty_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ignored = root / "docs/node_modules"
            ignored.mkdir(parents=True)
            (ignored / "dependency.md").write_text("# Dependency\n")

            result, _ = self.run_script(root, "check")

            self.assertEqual(result["summary"]["ignored_directories"], ["node_modules"])
            self.assertEqual(result["summary"]["markdown_files"], 0)
            self.assertIn("empty_bundle", {item["code"] for item in result["warnings"]})

    def test_scaffolded_section_descriptions_use_index_body_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.run_script(root, "scaffold")
            self.run_script(root, "index", "--write")

            root_index = (root / "docs/index.md").read_text()
            match = re.search(
                r"^\* \[decisions/\]\(decisions/\) - (.+)$",
                root_index,
                re.MULTILINE,
            )
            self.assertIsNotNone(match)
            assert match is not None
            self.assertTrue(match.group(1).strip())

    @unittest.skipUnless(os.name == "posix", "symlink tests require POSIX")
    def test_symlinked_index_does_not_satisfy_required_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "repo"
            self.scaffold_and_index(root)
            topic = root / "docs/topic"
            topic.mkdir()
            (topic / "guide.md").write_text(
                concept("Guide", "Topic Guide", "Topic documentation.")
            )
            outside = pathlib.Path(tmp) / "outside-index.md"
            outside_content = "# Outside Index\n"
            outside.write_text(outside_content)
            (topic / "index.md").symlink_to(outside)
            self.run_script(root, "index", "--write")

            result, _ = self.run_script(root, "check", expected_status=1)

            missing_indexes = [
                item["path"]
                for item in result["errors"]
                if item["code"] == "missing_index"
            ]
            self.assertEqual(missing_indexes, ["docs/topic/index.md"])
            self.assertEqual(outside.read_text(), outside_content)

    def test_root_level_markdown_requires_bundle_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text(
                concept("Guide", "Root Guide", "Root-level documentation.")
            )

            result, _ = self.run_script(root, "check", expected_status=1)

            missing_indexes = [
                item["path"]
                for item in result["errors"]
                if item["code"] == "missing_index"
            ]
            self.assertEqual(missing_indexes, ["docs/index.md"])

    def test_log_must_not_contain_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.scaffold_and_index(root)
            (root / "docs/log.md").write_text(
                "---\ntype: Guide\n---\n\n# Log\n\n## 2026-07-15\n\nChanged.\n"
            )

            result, _ = self.run_script(root, "check", expected_status=1)

            log_errors = [
                item for item in result["errors"] if item["path"] == "docs/log.md"
            ]
            self.assertEqual([item["code"] for item in log_errors], ["log_frontmatter"])

    def test_python_project_metadata_matches_skill_release(self):
        metadata = tomllib.loads(PYPROJECT_PATH.read_text())
        skill_md = SKILL_MD_PATH.read_text()
        skill_version = re.search(r'^\s+version: "([^"]+)"$', skill_md, re.MULTILINE)
        self.assertIsNotNone(skill_version, "SKILL.md must declare metadata.version")
        assert skill_version is not None

        self.assertEqual(metadata["project"]["name"], "easy-docs")
        self.assertEqual(metadata["project"]["version"], skill_version.group(1))
        self.assertEqual(
            metadata["project"]["authors"],
            [{"name": "Davi Mello", "email": "dsmello@ollem.io"}],
        )
        self.assertEqual(metadata["project"]["license"], "GPL-3.0-or-later")
        self.assertFalse(metadata["tool"]["uv"]["package"])


if __name__ == "__main__":
    unittest.main()

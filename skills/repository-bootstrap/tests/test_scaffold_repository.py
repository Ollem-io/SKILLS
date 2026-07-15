#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "scaffold_repository.py"
PYPROJECT_PATH = SKILL_ROOT / "pyproject.toml"
SKILL_MD_PATH = SKILL_ROOT / "SKILL.md"
# Resolve uv to a full path so subprocess calls do not rely on a bare name.
UV = shutil.which("uv") or "uv"


def load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold_repository", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scaffold = load_scaffold()

    def run_script(self, root: pathlib.Path, *args: str) -> dict:
        result = subprocess.run(
            [UV, "run", "--script", str(SCRIPT_PATH), "--root", str(root), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return json.loads(result.stdout)

    def test_monorepo_scaffold_creates_structure_and_docs_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = self.run_script(root, "--target", "monorepo")

            self.assertEqual(result["central_folder"], "components")
            for relative_path in [
                "AGENTS.md",
                "components/.gitkeep",
                "docs/index.md",
                "docs/component-guide.md",
                "Justfile",
                "mise.toml",
                "prek.toml",
                "readme.md",
                ".gitignore",
                "scripts/validate.py",
                ".github/dependabot.yml",
                ".github/workflows/main.yaml",
                ".github/workflows/workflow.validation.yml",
            ]:
                self.assertTrue((root / relative_path).exists(), relative_path)

            for relative_path in [
                "docs/references",
                "docs/decisions",
                "docs/design",
                "docs/exec-plans",
                "docs/testing.md",
                "docs/architecture.md",
                "docs/repo-standards.md",
                "docs/local-development.md",
            ]:
                self.assertFalse((root / relative_path).exists(), relative_path)

            prek = (root / "prek.toml").read_text()
            self.assertIn('files = "^(components|docs|scripts)/"', prek)

            docs_index = (root / "docs" / "index.md").read_text()
            self.assertIn('okf_version: "0.1"', docs_index)
            self.assertIn("<!-- BEGIN GENERATED DOCS INDEX -->", docs_index)
            self.assertIn("[Component Guide](component-guide.md)", docs_index)

            agents = (root / "AGENTS.md").read_text()
            self.assertIn("## Component Entrypoints", agents)
            self.assertIn("<!-- BEGIN GENERATED CORE DOCS -->", agents)
            self.assertNotIn("docs/references/docs-maintenance.md", agents)
            self.assertIn("`easy-docs` skill", agents)

            guide = (root / "docs" / "component-guide.md").read_text()
            self.assertIn("## Component Map", guide)
            self.assertIn("Tracker component value", guide)

    def test_python_project_metadata_matches_skill_release(self):
        metadata = tomllib.loads(PYPROJECT_PATH.read_text())
        skill_md = SKILL_MD_PATH.read_text()
        skill_version = re.search(r'^\s+version: "([^"]+)"$', skill_md, re.MULTILINE)
        assert skill_version is not None, "SKILL.md must declare metadata.version"

        self.assertEqual(metadata["project"]["name"], "repository-bootstrap")
        self.assertEqual(metadata["project"]["version"], skill_version.group(1))
        self.assertEqual(
            metadata["project"]["authors"],
            [{"name": "Davi Mello", "email": "dsmello@ollem.io"}],
        )
        self.assertFalse(metadata["tool"]["uv"]["package"])

    def test_adoption_plan_delegates_docs_system(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = self.run_script(root, "--target", "adopt")

            self.assertEqual(
                result["docs_system"],
                "delegate to easy-docs skill (OKF headers, generated indexes)",
            )
            self.assertEqual(
                result["missing_entrypoints"],
                ["AGENTS.md", "project.md", "docs/index.md"],
            )
            self.assertEqual(result["docs_gaps"], ["docs/index.md"])

    def test_sites_target_normalizes_domain_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = self.run_script(
                root, "--target", "sites", "--project-name", "ollem.io"
            )

            self.assertEqual(result["central_folder"], "sites")
            self.assertTrue((root / "sites" / "ollem-io" / ".gitkeep").exists())
            self.assertIn("## Site Entrypoints", (root / "AGENTS.md").read_text())

    def test_custom_target_requires_central_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = subprocess.run(
                [
                    UV,
                    "run",
                    "--script",
                    str(SCRIPT_PATH),
                    "--root",
                    str(root),
                    "--target",
                    "custom",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--central-folder is required", result.stderr)

    def test_custom_scaffold_creates_folder_and_watches_it_in_prek(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = self.run_script(
                root, "--target", "custom", "--central-folder", "apps"
            )

            self.assertEqual(result["central_folder"], "apps")
            self.assertTrue((root / "apps" / ".gitkeep").exists())
            self.assertTrue((root / "docs" / "structure-guide.md").exists())
            self.assertIn("## Target Entrypoints", (root / "AGENTS.md").read_text())
            prek = (root / "prek.toml").read_text()
            self.assertIn('files = "^(apps|docs|scripts)/"', prek)

    def test_custom_target_rejects_unusable_central_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = subprocess.run(
                [
                    UV,
                    "run",
                    "--script",
                    str(SCRIPT_PATH),
                    "--root",
                    str(root),
                    "--target",
                    "custom",
                    "--central-folder",
                    "!!!",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no usable folder characters", result.stderr)

    def test_import_target_is_alias_for_adopt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text('{"name":"app"}\n')

            result = self.run_script(root, "--target", "import")

            self.assertEqual(result["mode"], "adopt")
            self.assertFalse((root / "AGENTS.md").exists())

    def test_scaffolded_markdown_links_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.run_script(root, "--target", "monorepo")

            for relpath in ["AGENTS.md", "readme.md", "docs/index.md"]:
                broken = self.scaffold.broken_markdown_links(root, relpath)
                self.assertEqual(broken, [], f"broken links in {relpath}")

    def test_adopt_skips_vendored_and_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            app = root / "api"
            app.mkdir()
            (app / "package.json").write_text('{"name":"api"}\n')
            (app / "Readme.md").write_text("# api\n")
            vendored = root / "node_modules" / "lodash"
            vendored.mkdir(parents=True)
            (vendored / "package.json").write_text('{"name":"lodash"}\n')
            hidden = root / ".venv"
            hidden.mkdir()
            (hidden / "pyvenv.cfg").write_text("home = /usr\n")
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("name: CI\n")

            result = self.run_script(root, "--target", "adopt")

            self.assertIn("node_modules", result["skipped_dirs"])
            self.assertIn(".venv", result["skipped_dirs"])
            self.assertNotIn("node_modules", result["top_level_dirs"])
            files = result["files_seen"]
            self.assertIn("api/package.json", files)
            self.assertIn(".github/workflows/ci.yml", files)
            self.assertFalse(any(f.startswith("node_modules/") for f in files))
            self.assertFalse(any(f.startswith(".venv/") for f in files))
            candidate_paths = [c["path"] for c in result["candidate_entrypoints"]]
            self.assertNotIn("node_modules", candidate_paths)
            api = next(c for c in result["candidate_entrypoints"] if c["path"] == "api")
            self.assertTrue(api["has_readme"])
            self.assertNotIn("api", result["missing_entrypoint_readmes"])

    def test_rerun_is_idempotent_and_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.run_script(root, "--target", "site")
            agents_path = root / "AGENTS.md"
            agents_path.write_text("custom agents\n")

            result = self.run_script(root, "--target", "site")

            self.assertEqual(agents_path.read_text(), "custom agents\n")
            self.assertIn("AGENTS.md", result["existing"])
            self.assertEqual(result["created"], [])

    def test_adopt_reports_missing_entrypoints_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "app.py").write_text("print('hello')\n")
            app = root / "components" / "api"
            app.mkdir(parents=True)
            (app / "package.json").write_text('{"name":"api"}\n')

            result = self.run_script(root, "--target", "adopt")

            self.assertEqual(result["mode"], "adopt")
            self.assertIn("app.py", result["files_seen"])
            self.assertEqual(
                result["missing_entrypoints"],
                ["AGENTS.md", "project.md", "docs/index.md"],
            )
            self.assertEqual(
                result["candidate_entrypoints"][0]["path"], "components/api"
            )
            self.assertIn("package.json", result["candidate_entrypoints"][0]["markers"])
            self.assertIn("components/api", result["missing_entrypoint_readmes"])
            self.assertEqual(result["docs_gaps"], ["docs/index.md"])
            self.assertIn(
                "Which folders are deployable apps/components",
                result["migration_questions"][0],
            )
            self.assertFalse((root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()

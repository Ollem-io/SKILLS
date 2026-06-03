#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import tomllib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "scaffold_repository.py"
PYPROJECT_PATH = SKILL_ROOT / "pyproject.toml"


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
            ["uv", "run", "--script", str(SCRIPT_PATH), "--root", str(root), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return json.loads(result.stdout)

    def test_monorepo_scaffold_creates_docs_agents_and_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            result = self.run_script(root, "--target", "monorepo")

            self.assertEqual(result["central_folder"], "components")
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "components" / ".gitkeep").exists())
            self.assertTrue((root / "docs" / "index.md").exists())
            self.assertTrue((root / "docs" / "component-guide.md").exists())
            self.assertTrue(
                (root / "docs" / "references" / "docs-maintenance.md").exists()
            )
            self.assertTrue(
                (
                    root / "docs" / "references" / "entrypoint-readme-template.md"
                ).exists()
            )
            self.assertTrue((root / "Justfile").exists())
            self.assertTrue((root / "mise.toml").exists())
            self.assertTrue((root / "prek.toml").exists())
            self.assertTrue((root / "scripts" / "validate.py").exists())
            self.assertTrue((root / ".github" / "workflows" / "main.yaml").exists())
            agents = (root / "AGENTS.md").read_text()
            self.assertIn("## Component Entrypoints", agents)
            self.assertIn(
                "[Docs maintenance](docs/references/docs-maintenance.md)", agents
            )
            testing = (root / "docs" / "testing.md").read_text()
            self.assertIn("## Quick Test Map", testing)
            self.assertIn("Fast local gate", testing)

    def test_python_project_metadata_matches_skill_release(self):
        metadata = tomllib.loads(PYPROJECT_PATH.read_text())

        self.assertEqual(metadata["project"]["name"], "repository-bootstrap")
        self.assertEqual(metadata["project"]["version"], "0.4.0")
        self.assertEqual(
            metadata["project"]["authors"],
            [{"name": "Davi Mello", "email": "dsmello@ollem.io"}],
        )
        self.assertFalse(metadata["tool"]["uv"]["package"])

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
                    "uv",
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
            self.assertIn("AGENTS.md", result["missing_entrypoints"])
            self.assertIn(
                "docs/references/docs-maintenance.md", result["missing_entrypoints"]
            )
            self.assertEqual(
                result["candidate_entrypoints"][0]["path"], "components/api"
            )
            self.assertIn("package.json", result["candidate_entrypoints"][0]["markers"])
            self.assertIn("components/api", result["missing_entrypoint_readmes"])
            self.assertIn("docs/architecture.md", result["docs_gaps"])
            self.assertIn(
                "Which folders are deployable apps/components",
                result["migration_questions"][0],
            )
            self.assertFalse((root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()

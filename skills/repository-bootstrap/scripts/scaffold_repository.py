#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
import argparse
import json
import os
import re
from pathlib import Path


TARGETS = {"monorepo", "site", "sites", "custom", "adopt", "import"}


# Vendored, generated, and cache directories that adoption scans must skip so
# the JSON plan stays small enough to hand to an agent.
IGNORED_DIRS = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "venv",
    "__pycache__",
}


TARGET_GUIDE = {
    "monorepo": ("docs/component-guide.md", "Component Guide"),
    "site": ("docs/site-guide.md", "Site Guide"),
    "sites": ("docs/site-guide.md", "Site Guide"),
    "custom": ("docs/structure-guide.md", "Structure Guide"),
}


ENTRYPOINT_HEADINGS = {
    "monorepo": "Component Entrypoints",
    "site": "App Entrypoint",
    "sites": "Site Entrypoints",
    "custom": "Target Entrypoints",
}


ENTRYPOINT_MARKERS = {
    "package.json",
    "go.mod",
    "pyproject.toml",
    "Cargo.toml",
    "Justfile",
    "justfile",
    "mise.toml",
    "Dockerfile",
    "docker-compose.yml",
    "pnpm-lock.yaml",
    "uv.lock",
}


def placeholder(title: str) -> str:
    return f"# {title}\n\nPLACE HOLDER\n"


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = value.replace(".", "-")
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-_")


def is_ignored_dir(name: str) -> bool:
    if name == ".github":
        return False
    return name in IGNORED_DIRS or name.startswith(".")


def central_folder(target: str, custom_folder: str | None) -> str | None:
    if target == "monorepo":
        return "components"
    if target == "site":
        return "site"
    if target == "sites":
        return "sites"
    if target == "custom":
        if not custom_folder:
            raise SystemExit("--central-folder is required for --target custom")
        name = normalize_name(custom_folder)
        if not name:
            raise SystemExit(
                f"--central-folder {custom_folder!r} contains no usable folder characters"
            )
        return name
    return None


def target_guide(target: str) -> tuple[str, str] | None:
    return TARGET_GUIDE.get(target)


def docs_for_target(target: str) -> dict[str, str]:
    docs = {
        "project.md": placeholder("Project Specification"),
        "docs/index.md": render_docs_index(target),
    }
    guide = target_guide(target)
    if guide:
        relpath, title = guide
        docs[relpath] = render_target_guide(target, title)
    return docs


def tooling_for_target(folder: str | None) -> dict[str, str]:
    return {
        ".gitignore": render_gitignore(),
        "Justfile": render_justfile(),
        "mise.toml": render_mise_toml(),
        "prek.toml": render_prek_toml(folder),
        "scripts/validate.py": render_validate_py(),
        "scripts/benchmark_tests.py": render_benchmark_tests_py(),
        ".github/dependabot.yml": render_dependabot(),
        ".github/workflows/main.yaml": render_ci_dispatcher(),
        ".github/workflows/workflow.validation.yml": render_validation_workflow(),
    }


def render_docs_index(target: str) -> str:
    guide = target_guide(target)
    guide_sentence = (
        f" The target folder contract lives in [{guide[1]}]({Path(guide[0]).name})."
        if guide
        else ""
    )
    return f"""---
type: Index
title: Documentation Index
description: Repository documentation entrypoint and generated catalog.
okf_version: "0.1"
timestamp: 1970-01-01
---

# Documentation Index

This index is the entrypoint for repository documentation.{guide_sentence}

<!-- BEGIN GENERATED DOCS INDEX -->
<!-- END GENERATED DOCS INDEX -->

## Documentation Rules

- Keep root `docs/*.md` files at or below 500 lines.
- Run the `easy-docs` skill to maintain documentation headers and indexes.
"""


def render_justfile() -> str:
    return """set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    just --list

install:
    @echo "TODO: install repository dependencies"

fmt:
    @echo "TODO: run formatters"

lint:
    @echo "TODO: run linters"

check:
    @echo "TODO: run static, type, or security checks"

test-unit:
    @echo "TODO: run unit tests"

test-cov:
    @echo "TODO: run coverage tests"

test-smoke:
    @echo "TODO: run smoke tests"

build-dev:
    @echo "TODO: build development artifacts"

build-prod:
    @echo "TODO: build production artifacts"

validate:
    uv run --script scripts/validate.py all

validate-pre-commit:
    uv run --script scripts/validate.py pre-commit

benchmark-tests:
    uv run --script scripts/benchmark_tests.py
"""


def render_mise_toml() -> str:
    return """[settings]
minimum_release_age = "3d"

[tools]
python = "3.12"
uv = "latest"
just = "latest"
prek = "latest"
cocogitto = "latest"
# Add language toolchains when a target needs them, pinned to a major version:
# node = "22"
# pnpm = "latest"

[tasks.validate]
description = "Run the full local validation baseline."
run = "just validate"

[tasks.validate-pre-commit]
description = "Run the fast deterministic pre-commit validation baseline."
run = "just validate-pre-commit"

[tasks.benchmark-tests]
description = "Benchmark validation commands before widening hook scope."
run = "just benchmark-tests"
"""


def render_prek_toml(folder: str | None) -> str:
    watched = list(dict.fromkeys(filter(None, [folder, "docs", "scripts"])))
    target_pattern = "^(" + "|".join(watched) + ")/"
    return f"""#:schema https://www.schemastore.org/prek.json

minimum_prek_version = "0.3.13"
default_install_hook_types = ["pre-commit", "commit-msg"]

[[repos]]
repo = "local"
hooks = [
  {{
    id = "fast-quality-gates",
    name = "Run fast deterministic quality gates",
    language = "system",
    entry = "uv run --script scripts/validate.py pre-commit",
    files = "{target_pattern}",
    stages = ["pre-commit"],
    pass_filenames = false,
    require_serial = true,
  }},
  {{
    id = "cog-commit-message",
    name = "Validate Conventional Commit message",
    language = "system",
    entry = "mise exec -- cog verify --file",
    stages = ["commit-msg"],
    pass_filenames = true,
  }},
]
"""


def render_validate_py() -> str:
    return """#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
import argparse
import shutil
import subprocess
import sys


STEPS = {
    "install": ["just", "install"],
    "fmt": ["just", "fmt"],
    "lint": ["just", "lint"],
    "check": ["just", "check"],
    "test-unit": ["just", "test-unit"],
    "test-cov": ["just", "test-cov"],
    "test-smoke": ["just", "test-smoke"],
    "build-dev": ["just", "build-dev"],
    "build-prod": ["just", "build-prod"],
}

GROUPS = {
    "pre-commit": ["fmt", "lint", "test-unit"],
    "all": [
        "install",
        "fmt",
        "lint",
        "check",
        "test-unit",
        "test-cov",
        "test-smoke",
        "build-dev",
        "build-prod",
    ],
}


def just_recipes() -> set[str]:
    if not shutil.which("just"):
        return set()
    result = subprocess.run(["just", "--summary"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        return set()
    return set(result.stdout.split())


def run_group(group: str) -> int:
    recipes = just_recipes()
    failed = 0
    for step in GROUPS[group]:
        command = STEPS[step]
        recipe = command[1]
        if recipe not in recipes:
            print(f"skip {step}: just recipe '{recipe}' is not defined")
            continue
        print("run " + " ".join(command))
        completed = subprocess.run(command)
        if completed.returncode != 0:
            failed = completed.returncode
            break
    return failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=sorted(GROUPS), nargs="?", default="all")
    args = parser.parse_args()
    return run_group(args.group)


if __name__ == "__main__":
    sys.exit(main())
"""


def render_benchmark_tests_py() -> str:
    return """#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
import argparse
import shutil
import subprocess
import time


HEAVY_NAMES = ("e2e", "full", "docker", "browser")


def discover_recipes() -> list[str]:
    if not shutil.which("just"):
        return []
    result = subprocess.run(["just", "--summary"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        return []
    return sorted(recipe for recipe in result.stdout.split() if recipe.startswith("test-") or recipe == "validate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-heavy", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()

    status = 0
    for recipe in discover_recipes():
        if args.skip_heavy and any(name in recipe for name in HEAVY_NAMES):
            print(f"skip {recipe}: heavy")
            continue
        command = ["just", recipe]
        if args.dry_run:
            print("would run " + " ".join(command))
            continue
        start = time.monotonic()
        completed = subprocess.run(command)
        elapsed = time.monotonic() - start
        print(f"{recipe}: {elapsed:.2f}s rc={completed.returncode}")
        if completed.returncode != 0:
            status = completed.returncode
            if args.fail_fast:
                break
    return status


if __name__ == "__main__":
    raise SystemExit(main())
"""


def render_ci_dispatcher() -> str:
    return """name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  validation:
    uses: ./.github/workflows/workflow.validation.yml
"""


def render_validation_workflow() -> str:
    return """name: Reusable validation

on:
  workflow_call:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: jdx/mise-action@v2
        with:
          cache: true
      - run: just validate
"""


def render_target_guide(target: str, title: str) -> str:
    folder = (
        central_folder(target, "custom-folder")
        if target != "custom"
        else "<custom-folder>"
    )
    if target == "monorepo":
        contract = """- New components live under `components/<component-name>/`.
- Every component has a `readme.md` as its source of truth.
- Register new components in `AGENTS.md` and in the Component Map below.
- Expose local install, format, lint, test, smoke, and build commands when they
  apply.

## Component Map

Keep this table current; automation (issue trackers, agent pipelines,
component-aware concurrency) can rely on it as the canonical mapping.

| Folder | Language | Purpose | Tracker component value |
| --- | --- | --- | --- |
| PLACE HOLDER | PLACE HOLDER | PLACE HOLDER | PLACE HOLDER |"""
    elif target in {"site", "sites"}:
        contract = """- Website folders use stable names based on the main domain.
- Register new websites or major site entrypoints in `AGENTS.md`.
- Document local development, build, deploy, and validation commands.
- Ask before choosing a naming pattern for mobile or target-specific variants."""
    else:
        contract = """- Follow the user-provided folder contract.
- Register major entrypoints in `AGENTS.md`.
- Document local development and validation commands.
- Keep migration notes explicit when adopting an existing repository."""
    return f"""# {title}

This guide owns the folder contract for the `{target}` target.

## Central Folder

- `{folder}/`

## Entrypoint Contract

{contract}

## Definition Of Done

- The entrypoint folder exists.
- The entrypoint is linked from `AGENTS.md`.
- The relevant docs describe setup, validation, and ownership.
- The narrowest useful validation command passes or the blocker is documented.
"""


def render_readme(project_name: str | None) -> str:
    title = project_name or "PLACE HOLDER"
    return f"""# {title}

PLACE HOLDER

## Start Here

- [Agent entrypoint](AGENTS.md)
- [Documentation index](docs/index.md)
- [Project specification](project.md)

## Documentation

Run the `easy-docs` skill after bootstrap to create core guides and maintain
headers and indexes.
"""


def render_gitignore() -> str:
    return """# Python
__pycache__/
*.py[cod]
.venv/
venv/
.ruff_cache/
.pytest_cache/
.mypy_cache/

# Node
node_modules/

# Build artifacts
dist/
build/
coverage/

# Environment and editor
.env
.env.*
.DS_Store
"""


def render_dependabot() -> str:
    return """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
"""


def write_missing(
    root: Path,
    relative_path: str,
    content: str,
    created: list[str],
    existing: list[str],
) -> None:
    path = root / relative_path
    if path.exists():
        existing.append(relative_path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    created.append(relative_path)


def path_has_marker(path: Path) -> bool:
    return any((path / marker).exists() for marker in ENTRYPOINT_MARKERS)


def markers_for(path: Path) -> list[str]:
    return sorted(marker for marker in ENTRYPOINT_MARKERS if (path / marker).exists())


def has_readme(path: Path) -> bool:
    return any(
        child.is_file() and child.name.lower() == "readme.md"
        for child in path.iterdir()
    )


def visible_files(root: Path) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if not is_ignored_dir(name))
        relative = Path(dirpath).relative_to(root)
        for name in filenames:
            files.append(str(relative / name) if relative.parts else name)
    return sorted(files)


def candidate_dirs(root: Path) -> list[Path]:
    candidates = []
    search_roots = [root]
    for name in ["components", "apps", "packages", "services", "sites"]:
        directory = root / name
        if directory.is_dir():
            search_roots.extend(
                path
                for path in directory.iterdir()
                if path.is_dir() and not is_ignored_dir(path.name)
            )
    search_roots.extend(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name != "docs" and not is_ignored_dir(path.name)
    )
    for path in sorted(set(search_roots)):
        if path_has_marker(path):
            candidates.append(path)
    return candidates


def broken_markdown_links(root: Path, relative_path: str) -> list[str]:
    path = root / relative_path
    if not path.exists():
        return []
    links = re.findall(r"\[[^\]]+\]\(([^)#]+)", path.read_text())
    broken = []
    for link in links:
        if "://" in link or link.startswith("mailto:"):
            continue
        target = (path.parent / link).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        if not target.exists():
            broken.append(link)
    return sorted(set(broken))


def adoption_plan(root: Path) -> dict:
    files = visible_files(root)
    dirs = sorted(
        str(path.relative_to(root))
        for path in root.iterdir()
        if path.is_dir() and not is_ignored_dir(path.name)
    )
    skipped = sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and is_ignored_dir(path.name) and path.name != ".git"
    )
    missing = [
        item
        for item in ["AGENTS.md", "project.md", "docs/index.md"]
        if not (root / item).exists()
    ]
    detected_targets = [
        name
        for name in ["components", "site", "sites", "apps", "packages"]
        if (root / name).exists()
    ]
    candidates = [
        {
            "path": str(path.relative_to(root)),
            "markers": markers_for(path),
            "has_readme": has_readme(path),
        }
        for path in candidate_dirs(root)
    ]
    missing_readmes = [item["path"] for item in candidates if not item["has_readme"]]
    docs_gaps = [item for item in ["docs/index.md"] if not (root / item).exists()]
    return {
        "mode": "adopt",
        "files_seen": files,
        "top_level_dirs": dirs,
        "skipped_dirs": skipped,
        "detected_target_dirs": detected_targets,
        "candidate_entrypoints": candidates,
        "missing_entrypoint_readmes": missing_readmes,
        "missing_entrypoints": missing,
        "docs_gaps": docs_gaps,
        "docs_system": "delegate to easy-docs skill (OKF headers, generated indexes)",
        "broken_links": {
            "AGENTS.md": broken_markdown_links(root, "AGENTS.md"),
            "docs/index.md": broken_markdown_links(root, "docs/index.md"),
        },
        "migration_questions": [
            "Which folders are deployable apps/components versus libraries or support code?",
            "Should established names be preserved even if they do not match the preferred naming convention?",
            "Which command facade is canonical: just, mise, pnpm, uv, or another tool?",
            "Which docs are current source of truth versus historical or task artifacts?",
            "Should existing paths be registered in place, or is moving and renaming allowed?",
            "Which CI, Docker, deployment, and import paths must be updated if anything moves?",
            "What local validation must prove a move did not break runtime entrypoints?",
        ],
        "recommendations": [
            "map the existing repository before moving files",
            "create or update AGENTS.md from the existing repository structure",
            "create AGENTS.md, project.md, and docs/index.md, then run easy-docs",
            "choose monorepo, site, sites, or custom before moving existing files",
            "register existing entrypoints in place unless the user approves a migration",
            "explain required file moves, docs updates, and validation commands before applying them",
            "preserve existing files unless the user approves a migration",
        ],
    }


def scaffold(
    root: Path, target: str, project_name: str | None, custom_folder: str | None
) -> dict:
    created: list[str] = []
    existing: list[str] = []
    folder = central_folder(target, custom_folder)

    for relpath, content in sorted(docs_for_target(target).items()):
        write_missing(root, relpath, content, created, existing)
    for relpath, content in sorted(tooling_for_target(folder).items()):
        write_missing(root, relpath, content, created, existing)
    write_missing(root, "readme.md", render_readme(project_name), created, existing)

    folder_entries: list[str] = []
    if folder:
        write_missing(root, f"{folder}/.gitkeep", "", created, existing)
        folder_entries.append(folder)
        if target == "sites" and project_name:
            site_name = normalize_name(project_name) or "site"
            write_missing(root, f"{folder}/{site_name}/.gitkeep", "", created, existing)
            folder_entries.append(f"{folder}/{site_name}")

    agents = render_agents(target, folder_entries)
    write_missing(root, "AGENTS.md", agents, created, existing)

    return {
        "mode": "scaffold",
        "target": target,
        "central_folder": folder,
        "created": sorted(created),
        "existing": sorted(existing),
    }


def render_agents(target: str, folder_entries: list[str]) -> str:
    guide = target_guide(target)
    guide_line = f"- Folder contract: [{guide[1]}]({guide[0]})\n" if guide else ""
    folder_links = "\n".join(
        f"- `{entry}/` - target folder." for entry in folder_entries
    )
    if not folder_links:
        folder_links = "- Target folder: PLACE HOLDER"
    heading = ENTRYPOINT_HEADINGS.get(target, "Target Entrypoints")

    return f"""# Agent Entrypoint

`AGENTS.md` is a map, not a manual. Keep this file short so agents can load it
first, then choose the right repo-local source of truth.

## Start Here

- [Documentation index](docs/index.md) - documentation entrypoint and generated
  catalog.
- [Specification](project.md) - product or repository specification.

<!-- BEGIN GENERATED CORE DOCS -->
<!-- END GENERATED CORE DOCS -->

## {heading}

- Type: `{target}`
{guide_line}{folder_links}

## Must Follow

- Documentation must flow `docs/` -> topic file -> topic folder when needed.
- Any `.md` file directly under `docs/` must stay at or below 500 lines.
- If a root `docs/*.md` topic would exceed 500 lines, create a folder with the
  same base name and move detailed content there.
- Every specialized documentation folder must include an `index.md`.
- Documentation system (headers, indexes, and docs rules) is owned by the
  `easy-docs` skill; run it after structural changes.
- Update `AGENTS.md`, `docs/index.md`, and the relevant target guide when adding
  or moving entrypoints.
- Use deterministic scripts and tests for repository tooling.
- Run the narrowest available validation before delivery.
- Use Conventional Commit messages: `type(scope): description`.
- Do not commit secrets, production data, or sensitive incident evidence.

## Definition Of Done

- Follow the task-specific Definition of Done in the relevant source of truth.
- New entrypoints are registered in this file and linked to their docs.
- Required validation has passed or the blocker is documented.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="repository root to scaffold")
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument("--project-name", help="site domain or project name")
    parser.add_argument("--central-folder", help="custom central folder")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.target in {"adopt", "import"}:
        result = adoption_plan(root)
    else:
        result = scaffold(root, args.target, args.project_name, args.central_folder)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

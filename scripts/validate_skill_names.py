#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Validate skill frontmatter against the Agent Skills standard.

Reference: docs/references/agent-skills-standard.md
(https://agentskills.io/specification).

For each `skills/<dir>/SKILL.md` (or lowercase `skill.md`) this checks:

- Frontmatter is a YAML mapping fenced by `---` lines.
- Only the spec's allowed top-level fields are present.
- `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$` (we keep the spec's ASCII subset:
  lowercase letters, digits, single hyphens; no leading/trailing/consecutive
  hyphen), is at most 64 characters, and equals the skill directory name.
- `description` is a non-empty string at most 1024 characters.
- `compatibility`, when present, is a string at most 500 characters.

All issues for a skill are reported together rather than failing on the first.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

NAME_PATTERN_TEXT = r"^[a-z0-9]+(-[a-z0-9]+)*$"
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}
EXPECTED = (
    "frontmatter is a YAML mapping using only "
    f"{sorted(ALLOWED_FIELDS)}; name matches {NAME_PATTERN_TEXT} (<= "
    f"{MAX_NAME_LENGTH} chars, equals the directory name); description is a "
    f"non-empty string <= {MAX_DESCRIPTION_LENGTH} chars; compatibility, if "
    f"present, is a string <= {MAX_COMPATIBILITY_LENGTH} chars"
)

NAME_PATTERN = re.compile(NAME_PATTERN_TEXT)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_skill_md(skill_dir: Path) -> Path | None:
    """Prefer uppercase SKILL.md, accept lowercase skill.md (spec behavior)."""
    for candidate in ("SKILL.md", "skill.md"):
        path = skill_dir / candidate
        if path.is_file():
            return path
    return None


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, error). error is empty on success."""
    if not text.startswith("---"):
        return None, "missing frontmatter (file must start with `---`)"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter (missing closing `---`)"
    try:
        loaded = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if loaded is None:
        return None, "empty frontmatter"
    if not isinstance(loaded, dict):
        return None, "frontmatter must be a YAML mapping"
    return loaded, ""


def _validate_name(name: object, dir_name: str, issues: list[str]) -> object:
    if not isinstance(name, str) or not name:
        issues.append("`name` must be a non-empty string")
        return name
    if not NAME_PATTERN.match(name):
        issues.append(
            f"name '{name}' must match {NAME_PATTERN_TEXT} (lowercase letters, "
            "digits, single hyphens; no underscores, uppercase, or "
            "leading/trailing/consecutive hyphen)"
        )
    if len(name) > MAX_NAME_LENGTH:
        issues.append(f"name '{name}' exceeds {MAX_NAME_LENGTH} characters")
    if name != dir_name:
        issues.append(
            f"name '{name}' must equal the skill directory name '{dir_name}'"
        )
    return name


def _validate_description(description: object, issues: list[str]) -> None:
    if not isinstance(description, str) or not description.strip():
        issues.append("`description` must be a non-empty string")
        return
    if len(description) > MAX_DESCRIPTION_LENGTH:
        issues.append(
            f"description exceeds {MAX_DESCRIPTION_LENGTH} characters "
            f"(is {len(description)})"
        )


def _validate_compatibility(compatibility: object, issues: list[str]) -> None:
    if not isinstance(compatibility, str):
        issues.append("`compatibility` must be a string")
        return
    if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        issues.append(
            f"compatibility exceeds {MAX_COMPATIBILITY_LENGTH} characters "
            f"(is {len(compatibility)})"
        )


def evaluate_skill(skill_dir: Path) -> dict:
    dir_name = skill_dir.name
    issues: list[str] = []
    name: object = None

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        issues.append("missing SKILL.md (or skill.md)")
        return {"skill": dir_name, "name": None, "ok": False, "issues": issues}

    frontmatter, error = parse_frontmatter(skill_md.read_text())
    if error:
        issues.append(error)
        return {"skill": dir_name, "name": None, "ok": False, "issues": issues}

    assert frontmatter is not None
    extra = sorted(set(frontmatter) - ALLOWED_FIELDS)
    if extra:
        issues.append(
            f"unexpected frontmatter fields {extra}; only "
            f"{sorted(ALLOWED_FIELDS)} are allowed"
        )

    if "name" not in frontmatter:
        issues.append("missing required field `name`")
    else:
        name = _validate_name(frontmatter["name"], dir_name, issues)

    if "description" not in frontmatter:
        issues.append("missing required field `description`")
    else:
        _validate_description(frontmatter["description"], issues)

    if "compatibility" in frontmatter:
        _validate_compatibility(frontmatter["compatibility"], issues)

    return {
        "skill": dir_name,
        "name": name if isinstance(name, str) else None,
        "ok": not issues,
        "issues": issues,
    }


def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir():
        return []
    return sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and find_skill_md(path) is not None
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-root",
        default=str(repo_root() / "skills"),
        help="directory containing one skill per subfolder",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    args = parser.parse_args()

    skills_root = Path(args.skills_root).resolve()
    skills = discover_skills(skills_root)
    results = [evaluate_skill(skill_dir) for skill_dir in skills]
    failures = [r for r in results if not r["ok"]]

    if args.json:
        print(
            json.dumps(
                {"expected": EXPECTED, "results": results, "failures": len(failures)},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"expected: {EXPECTED}")
        if not results:
            print(f"no skills found under {skills_root}")
        for result in results:
            status = "ok" if result["ok"] else "FAIL"
            print(f"[{status}] {result['skill']} (name: {result['name']})")
            for issue in result["issues"]:
                print(f"       - {issue}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

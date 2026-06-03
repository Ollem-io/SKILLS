#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Validate that every skill name follows the Agent Skills naming standard.

Expected for each `skills/<dir>/SKILL.md`:

- The frontmatter `name:` field is present.
- `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase letters, digits, and
  single hyphens; no underscores, spaces, uppercase, or leading/trailing
  hyphen) and is at most 64 characters.
- `name` equals the skill directory name so links and invocation stay in sync.
"""
import argparse
import json
import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
EXPECTED = (
    "name matches ^[a-z0-9]+(-[a-z0-9]+)*$ (lowercase, digits, single hyphens; "
    "no underscores), is <= 64 chars, and equals the skill directory name"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    for line in parts[1].splitlines():
        match = re.match(r"\s*name\s*:\s*(.+?)\s*$", line)
        if match:
            return match.group(1).strip().strip("'\"")
    return None


def evaluate_skill(skill_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    dir_name = skill_dir.name
    name = read_frontmatter_name(skill_md)
    issues: list[str] = []

    if name is None:
        issues.append("missing frontmatter `name` field")
    else:
        if not NAME_PATTERN.match(name):
            issues.append(
                f"name '{name}' must match ^[a-z0-9]+(-[a-z0-9]+)*$ "
                "(use lowercase letters, digits, and single hyphens; no underscores)"
            )
        if len(name) > MAX_NAME_LENGTH:
            issues.append(f"name '{name}' exceeds {MAX_NAME_LENGTH} characters")
        if name != dir_name:
            issues.append(
                f"name '{name}' must equal the skill directory name '{dir_name}'"
            )

    return {
        "skill": dir_name,
        "name": name,
        "ok": not issues,
        "issues": issues,
    }


def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir():
        return []
    return sorted(
        path for path in skills_root.iterdir() if (path / "SKILL.md").is_file()
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

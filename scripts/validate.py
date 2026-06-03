#!/usr/bin/env -S uv run --script
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
    "validate-skill-names": ["just", "validate-skill-names"],
    "check": ["just", "check"],
    "test-unit": ["just", "test-unit"],
    "test-cov": ["just", "test-cov"],
    "test-smoke": ["just", "test-smoke"],
    "build-dev": ["just", "build-dev"],
    "build-prod": ["just", "build-prod"],
}

GROUPS = {
    "pre-commit": ["fmt", "lint", "validate-skill-names", "test-unit"],
    "all": [
        "install",
        "fmt",
        "lint",
        "validate-skill-names",
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

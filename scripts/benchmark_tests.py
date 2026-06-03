#!/usr/bin/env -S uv run --script
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

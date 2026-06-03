set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Upstream Agent Skills reference validator (skills-ref), pinned by commit.
# Source: https://github.com/agentskills/agentskills (subdirectory: skills-ref).
skills_ref_ref := "5d4c1fda3f786fff826c7f56b6cb3341e7f3a911"

default:
    just --list

install:
    @echo "TODO: install repository dependencies"

# Run a recipe in every skill that defines it, with a shared uv cache.
_each recipe:
    @for justfile in skills/*/Justfile; do \
      skill_dir="$(dirname "$justfile")"; \
      if (cd "$skill_dir" && just --summary 2>/dev/null | tr ' ' '\n' | grep -qx "{{recipe}}"); then \
        echo "{{recipe}} $skill_dir"; \
        (cd "$skill_dir" && UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" just "{{recipe}}"); \
      else \
        echo "skip $skill_dir: no {{recipe}} recipe"; \
      fi; \
    done

fmt:
    @just _each fmt

lint:
    @just _each lint

# Repository-wide Markdown linter (config: .markdownlint-cli2.jsonc).
lint-md:
    markdownlint-cli2

check:
    @just _each check

validate-skill-names:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script scripts/validate_skill_names.py

# Validate every skill against the full upstream Agent Skills standard.
validate-skill-spec:
    @found=0; \
    for skill_dir in skills/*/; do \
      if [ -f "$skill_dir/SKILL.md" ] || [ -f "$skill_dir/skill.md" ]; then \
        found=1; \
        echo "skills-ref validate $skill_dir"; \
        UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uvx --from "git+https://github.com/agentskills/agentskills.git@{{skills_ref_ref}}#subdirectory=skills-ref" skills-ref validate "$skill_dir"; \
      fi; \
    done; \
    if [ "$found" = "0" ]; then echo "no skills found under skills/"; fi

test-unit:
    @for justfile in skills/*/Justfile; do \
      skill_dir="$(dirname "$justfile")"; \
      echo "run $skill_dir: just test"; \
      (cd "$skill_dir" && UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" just test); \
    done

test-scripts:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script tests/test_validate_skill_names.py

test:
    just test-scripts
    just test-unit

test-cov:
    @echo "TODO: run coverage tests"

test-smoke:
    @echo "TODO: run smoke tests"

build-dev:
    @echo "TODO: build development artifacts"

build-prod:
    @echo "TODO: build production artifacts"

validate:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script scripts/validate.py all

validate-pre-commit:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script scripts/validate.py pre-commit

benchmark-tests:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script scripts/benchmark_tests.py

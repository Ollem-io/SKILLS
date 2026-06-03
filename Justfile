set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

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

validate-skill-names:
    UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" uv run --script scripts/validate_skill_names.py

test-unit:
    @for justfile in skills/*/Justfile; do \
      skill_dir="$(dirname "$justfile")"; \
      echo "run $skill_dir: just test"; \
      (cd "$skill_dir" && UV_CACHE_DIR="{{justfile_directory()}}/.uv-cache" just test); \
    done

test:
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

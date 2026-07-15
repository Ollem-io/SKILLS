#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

import argparse
import datetime
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml  # ty: ignore[unresolved-import]

GENERATED_INDEX_BEGIN = "<!-- BEGIN GENERATED DOCS INDEX -->"
GENERATED_INDEX_END = "<!-- END GENERATED DOCS INDEX -->"
GENERATED_CORE_BEGIN = "<!-- BEGIN GENERATED CORE DOCS -->"
GENERATED_CORE_END = "<!-- END GENERATED CORE DOCS -->"
RESERVED_FILENAMES = {"index.md", "log.md"}
IGNORED_DIRECTORIES = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "venv",
    "__pycache__",
}
CORE_GUIDES = {
    "architecture.md": (
        "Architecture",
        "System shape, runtime surfaces, and architectural boundaries.",
    ),
    "repo-standards.md": (
        "Repository Standards",
        "Repository-wide structure, naming, and workflow rules.",
    ),
    "local-development.md": (
        "Local Development",
        "Local setup, toolchain, and development commands.",
    ),
    "testing.md": ("Testing", "Test strategy and required validation commands."),
    "validation-loop.md": (
        "Validation Loop",
        "Validation-first workflow for repository changes.",
    ),
    "observability.md": (
        "Observability",
        "Logging, metrics, tracing, and debugging evidence guidance.",
    ),
    "security.md": (
        "Security",
        "Security policy, data handling, and trust boundaries.",
    ),
    "reliability.md": (
        "Reliability",
        "Reliability, recovery, and operational expectations.",
    ),
    "release-process.md": (
        "Release Process",
        "Branch, release, and deployment expectations.",
    ),
    "pr-review-workflow.md": (
        "PR Review Workflow",
        "Pull request review and validation workflow.",
    ),
    "merge-policy.md": ("Merge Policy", "Merge requirements and rollback policy."),
    "cleanup-workflow.md": (
        "Cleanup Workflow",
        "Routine cleanup and documentation maintenance workflow.",
    ),
    "engineering-maintenance.md": (
        "Engineering Maintenance",
        "Maintenance rules for engineering assets and automation.",
    ),
}
SPECIALIZED_SECTIONS = {
    "decisions": ("Decision Records", "Durable decisions and their rationale."),
    "design": ("Design Documents", "Detailed designs and technical proposals."),
    "exec-plans": ("Execution Plans", "Resumable plans for multi-step work."),
    "references": ("References", "Supporting templates and reference material."),
}

Frontmatter = dict[str, Any]


def is_ignored_directory(name: str) -> bool:
    return name.startswith(".") or name in IGNORED_DIRECTORIES


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def resolve_bundle(root: Path, value: str) -> tuple[Path, str]:
    bundle_value = Path(value)
    if bundle_value.is_absolute():
        bundle = bundle_value.resolve()
    else:
        bundle = (root / bundle_value).resolve()
    try:
        bundle_relative = bundle.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError("bundle must be inside root") from error
    if bundle == root:
        raise ValueError("bundle must be a directory below root")
    return bundle, bundle_relative


def iter_markdown_files(
    bundle: Path,
    ignored_directories: list[Path] | None = None,
) -> list[Path]:
    if not bundle.exists():
        return []
    files: list[Path] = []
    for current, directories, filenames in os.walk(bundle, followlinks=False):
        current_path = Path(current)
        if ignored_directories is not None:
            ignored_directories.extend(
                current_path / name
                for name in directories
                if is_ignored_directory(name)
            )
        directories[:] = sorted(
            name for name in directories if not is_ignored_directory(name)
        )
        files.extend(
            path
            for name in filenames
            if name.lower().endswith(".md")
            and not (path := current_path / name).is_symlink()
        )
    return sorted(files, key=lambda path: path.as_posix().casefold())


def parse_frontmatter(text: str) -> tuple[str, Frontmatter | None, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "missing", None, text
    end_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )
    if end_index is None:
        return "invalid", None, text
    yaml_text = "".join(lines[1:end_index])
    try:
        loaded = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return "invalid", None, text
    if not isinstance(loaded, dict):
        return "invalid", None, text
    return "valid", loaded, "".join(lines[end_index + 1 :])


def frontmatter_text(metadata: Frontmatter) -> str:
    rendered = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()
    return f"---\n{rendered}\n---\n"


def fallback_title(path: Path) -> str:
    words = path.stem.replace("-", " ").replace("_", " ")
    return words.title()


def first_heading(body: str) -> str | None:
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return None


def first_prose_line(body: str) -> str | None:
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if (
            in_fence
            or not stripped
            or stripped.startswith("#")
            or stripped.startswith("<!--")
            or re.match(r"^(?:[-*+] |\d+[.)] )", stripped)
        ):
            continue
        return stripped[:160]
    return None


def derived_type(path: Path, bundle: Path) -> str:
    relative = path.relative_to(bundle)
    first_segment = relative.parts[0] if len(relative.parts) > 1 else ""
    return {
        "decisions": "Decision Record",
        "design": "Design Doc",
        "exec-plans": "Execution Plan",
        "references": "Reference",
    }.get(first_segment, "Guide")


def git_timestamp(root: Path, path: Path, default_date: str) -> str:
    try:
        path_argument = path.relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%cs", "--", path_argument],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, ValueError):
        return default_date
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else default_date


def write_missing(
    root: Path,
    path: Path,
    content: str,
    created: list[str],
    existing: list[str],
) -> None:
    relpath = relative_path(path, root)
    if path.is_symlink() or path.exists():
        existing.append(relpath)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    created.append(relpath)


def render_concept(
    concept_type: str,
    title: str,
    description: str,
    timestamp: str,
    body: str,
    *,
    extra: Frontmatter | None = None,
) -> str:
    metadata: Frontmatter = {
        "type": concept_type,
        "title": title,
        "description": description,
    }
    if extra:
        metadata.update(extra)
    metadata["timestamp"] = timestamp
    return f"{frontmatter_text(metadata)}\n{body.rstrip()}\n"


def scaffold_command(
    root: Path, bundle: Path, bundle_relative: str, default_date: str
) -> tuple[dict[str, Any], int]:
    created: list[str] = []
    existing: list[str] = []
    root_index = render_concept(
        "Index",
        "Documentation Index",
        "Complete catalog of repository documentation.",
        default_date,
        "Repository documentation is cataloged below.\n\n"
        f"{GENERATED_INDEX_BEGIN}\n{GENERATED_INDEX_END}",
        extra={"okf_version": "0.1"},
    ).replace("okf_version: '0.1'", 'okf_version: "0.1"', 1)
    write_missing(root, bundle / "index.md", root_index, created, existing)

    for filename, (title, description) in sorted(CORE_GUIDES.items()):
        content = render_concept(
            "Guide",
            title,
            description,
            default_date,
            f"# {title}\n\nPLACE HOLDER",
        )
        write_missing(root, bundle / filename, content, created, existing)

    for folder, (title, description) in sorted(SPECIALIZED_SECTIONS.items()):
        content = (
            f"# {title}\n\n{description}\n\n"
            f"{GENERATED_INDEX_BEGIN}\n{GENERATED_INDEX_END}\n"
        )
        write_missing(root, bundle / folder / "index.md", content, created, existing)

    maintenance = render_concept(
        "Reference",
        "Docs Maintenance",
        "Ownership and update rules for the repository documentation system.",
        default_date,
        """# Docs Maintenance

## Update Rules

- Update `AGENTS.md` whenever repository entrypoints change.
- Regenerate indexes with `easy_docs.py index --write`; never hand-edit generated regions.
- Keep every root-level documentation file at or below 500 lines.
- Give every specialized documentation folder its own `index.md`.
""",
    )
    write_missing(
        root,
        bundle / "references" / "docs-maintenance.md",
        maintenance,
        created,
        existing,
    )

    sections = [
        "Purpose",
        "Runtime Surface",
        "Setup",
        "Commands",
        "Architecture Notes",
        "Tests",
        "Environment Variables",
        "External Dependencies",
        "Definition of Done",
    ]
    template_body = "# Entrypoint Readme Template\n\n" + "\n\n".join(
        f"## {section}\n\nPLACE HOLDER" for section in sections
    )
    template = render_concept(
        "Reference",
        "Entrypoint Readme Template",
        "Standard documentation template for repository entrypoints.",
        default_date,
        template_body,
    )
    write_missing(
        root,
        bundle / "references" / "entrypoint-readme-template.md",
        template,
        created,
        existing,
    )

    return (
        {
            "bundle": bundle_relative,
            "created": sorted(created),
            "existing": sorted(existing),
            "mode": "scaffold",
        },
        0,
    )


def headers_command(
    root: Path,
    bundle: Path,
    action: str,
    default_date: str,
) -> tuple[dict[str, Any], int]:
    missing: list[str] = []
    invalid: list[str] = []
    written: list[str] = []
    conformant = 0
    concept_files = [
        path
        for path in iter_markdown_files(bundle)
        if path.name not in RESERVED_FILENAMES
    ]
    for path in concept_files:
        relpath = relative_path(path, root)
        original = path.read_text()
        status, _, body = parse_frontmatter(original)
        if status == "invalid":
            invalid.append(relpath)
            continue
        if status == "valid":
            conformant += 1
            continue
        missing.append(relpath)
        if action != "write":
            continue
        metadata: Frontmatter = {
            "type": derived_type(path, bundle),
            "title": first_heading(body) or fallback_title(path),
        }
        description = first_prose_line(body)
        if description:
            metadata["description"] = description
        metadata["timestamp"] = git_timestamp(root, path, default_date)
        path.write_text(f"{frontmatter_text(metadata)}\n{original}")
        written.append(relpath)
        conformant += 1

    result: dict[str, Any] = {
        "conformant": conformant,
        "invalid": sorted(invalid),
        "missing": sorted(missing),
        "mode": "headers",
        "total": len(concept_files),
    }
    if action == "write":
        result["written"] = sorted(written)
    failures = invalid or (action == "check" and missing)
    return result, int(bool(failures))


def contains_markdown(directory: Path) -> bool:
    return bool(iter_markdown_files(directory))


def direct_concept_files(directory: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in directory.iterdir()
            if not path.is_symlink()
            and path.is_file()
            and path.name.lower().endswith(".md")
            and path.name not in RESERVED_FILENAMES
        ),
        key=lambda path: path.name.casefold(),
    )


def immediate_markdown_sections(directory: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in directory.iterdir()
            if not path.is_symlink()
            and path.is_dir()
            and not is_ignored_directory(path.name)
            and contains_markdown(path)
        ),
        key=lambda path: path.name.casefold(),
    )


def metadata_value(metadata: Frontmatter | None, key: str) -> str:
    if not metadata:
        return ""
    value = metadata.get(key)
    return str(value).strip() if value is not None else ""


def document_catalog_data(path: Path, bundle: Path) -> tuple[str, str, str]:
    status, metadata, body = parse_frontmatter(path.read_text())
    if status != "valid":
        metadata = None
        body = path.read_text()
    concept_type = metadata_value(metadata, "type") or derived_type(path, bundle)
    title = (
        metadata_value(metadata, "title") or first_heading(body) or fallback_title(path)
    )
    description = metadata_value(metadata, "description")
    return concept_type, title, description


def format_entry(title: str, link: str, description: str) -> str:
    entry = f"* [{title}]({link})"
    return f"{entry} - {description}" if description else entry


def render_catalog(
    directory: Path,
    bundle: Path,
    *,
    link_prefix: str = "",
    include_sections: bool = True,
) -> str:
    grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path in direct_concept_files(directory):
        concept_type, title, description = document_catalog_data(path, bundle)
        grouped[concept_type].append((title, f"{link_prefix}{path.name}", description))

    blocks: list[str] = []
    for concept_type in sorted(grouped, key=str.casefold):
        entries = sorted(grouped[concept_type], key=lambda item: item[0].casefold())
        block = [f"## {concept_type}"]
        block.extend(
            format_entry(title, link, description)
            for title, link, description in entries
        )
        blocks.append("\n\n".join([block[0], "\n".join(block[1:])]))

    if include_sections:
        section_entries: list[str] = []
        for section in immediate_markdown_sections(directory):
            index_path = section / "index.md"
            description = ""
            if index_path.is_file() and not index_path.is_symlink():
                status, metadata, body = parse_frontmatter(index_path.read_text())
                if status == "valid":
                    description = metadata_value(metadata, "description")
                description = description or first_prose_line(body) or ""
            section_entries.append(
                format_entry(f"{section.name}/", f"{section.name}/", description)
            )
        if section_entries:
            blocks.append("## Sections\n\n" + "\n".join(section_entries))

    return "\n\n".join(blocks)


def replace_generated_region(
    text: str, begin_marker: str, end_marker: str, generated: str
) -> str | None:
    if text.count(begin_marker) != 1 or text.count(end_marker) != 1:
        return None
    begin = text.index(begin_marker)
    end = text.find(end_marker, begin + len(begin_marker))
    if end == -1:
        return None
    before = text[: begin + len(begin_marker)]
    after = text[end:]
    middle = f"\n{generated}\n" if generated else "\n"
    return before + middle + after


def index_candidates(bundle: Path) -> list[Path]:
    return [
        path
        for path in iter_markdown_files(bundle)
        if path.name == "index.md" and not path.is_symlink()
    ]


def index_changes(
    root: Path, bundle: Path, bundle_relative: str
) -> tuple[list[tuple[Path, str]], list[str], list[str]]:
    changes: list[tuple[Path, str]] = []
    unmanaged: list[str] = []
    malformed: list[str] = []
    for index_path in index_candidates(bundle):
        original = index_path.read_text()
        catalog = render_catalog(index_path.parent, bundle)
        updated = replace_generated_region(
            original, GENERATED_INDEX_BEGIN, GENERATED_INDEX_END, catalog
        )
        relative = relative_path(index_path, root)
        if updated is None:
            if GENERATED_INDEX_BEGIN in original or GENERATED_INDEX_END in original:
                malformed.append(relative)
            else:
                unmanaged.append(relative)
        elif updated != original:
            changes.append((index_path, updated))

    agents_path = root / "AGENTS.md"
    if agents_path.is_file() and not agents_path.is_symlink():
        original = agents_path.read_text()
        prefix = f"{bundle_relative.rstrip('/')}/"
        catalog = render_catalog(
            bundle, bundle, link_prefix=prefix, include_sections=False
        )
        updated = replace_generated_region(
            original, GENERATED_CORE_BEGIN, GENERATED_CORE_END, catalog
        )
        relative = relative_path(agents_path, root)
        if updated is None:
            if GENERATED_CORE_BEGIN in original or GENERATED_CORE_END in original:
                malformed.append(relative)
            else:
                unmanaged.append(relative)
        elif updated != original:
            changes.append((agents_path, updated))
    return (
        sorted(changes, key=lambda item: item[0].as_posix()),
        sorted(unmanaged),
        sorted(malformed),
    )


def index_command(
    root: Path,
    bundle: Path,
    bundle_relative: str,
    action: str,
) -> tuple[dict[str, Any], int]:
    changes, unmanaged, malformed = index_changes(root, bundle, bundle_relative)
    changed_paths = [relative_path(path, root) for path, _ in changes]
    result: dict[str, Any] = {
        "malformed": malformed,
        "mode": "index",
        "unmanaged": unmanaged,
    }
    if action == "write":
        for path, content in changes:
            path.write_text(content)
        result["written"] = changed_paths
        return result, int(bool(malformed))
    result["drifted"] = changed_paths
    return result, int(bool(changed_paths or malformed))


def error(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def warning(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def directories_requiring_indexes(bundle: Path) -> list[Path]:
    markdown_files = iter_markdown_files(bundle)
    directories: set[Path] = {bundle} if markdown_files else set()
    for markdown in markdown_files:
        current = markdown.parent
        while current != bundle:
            directories.add(current)
            current = current.parent
    return sorted(directories, key=lambda path: path.as_posix().casefold())


def markdown_link_targets(text: str) -> list[str]:
    return re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)


def normalize_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    if " " in target:
        target = target.split(" ", 1)[0]
    return target


def broken_links(root: Path, bundle: Path, path: Path) -> list[str]:
    broken: list[str] = []
    for raw_target in markdown_link_targets(path.read_text()):
        target = normalize_link_target(raw_target)
        if (
            not target
            or "://" in target
            or target.startswith("mailto:")
            or target.startswith("#")
        ):
            continue
        target_without_anchor = target.split("#", 1)[0]
        if not target_without_anchor:
            continue
        if target_without_anchor.startswith("/"):
            resolved = (bundle / target_without_anchor.lstrip("/")).resolve()
        else:
            resolved = (path.parent / target_without_anchor).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            broken.append(target)
            continue
        if not resolved.exists():
            broken.append(target)
    return sorted(set(broken))


def check_command(
    root: Path, bundle: Path, bundle_relative: str
) -> tuple[dict[str, Any], int]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    ignored_directories: list[Path] = []
    markdown_files = iter_markdown_files(bundle, ignored_directories)
    concept_count = 0

    if not markdown_files:
        warnings.append(
            warning(
                "empty_bundle",
                relative_path(bundle, root),
                "Bundle contains no markdown documents.",
            )
        )

    for path in markdown_files:
        relpath = relative_path(path, root)
        text = path.read_text()
        status, metadata, _ = parse_frontmatter(text)
        is_reserved = path.name in RESERVED_FILENAMES
        if status == "invalid":
            errors.append(
                error(
                    "invalid_frontmatter",
                    relpath,
                    "YAML frontmatter is invalid or unterminated.",
                )
            )
        elif path.name == "index.md" and path.parent != bundle and status == "valid":
            errors.append(
                error(
                    "index_frontmatter",
                    relpath,
                    "Only the bundle-root index.md may contain frontmatter (OKF §6/§11).",
                )
            )
        elif path.name == "log.md" and status == "valid":
            errors.append(
                error(
                    "log_frontmatter",
                    relpath,
                    "log.md must not contain frontmatter.",
                )
            )
        elif not is_reserved:
            concept_count += 1
            if status == "missing":
                errors.append(
                    error(
                        "missing_frontmatter",
                        relpath,
                        "Concept document is missing YAML frontmatter.",
                    )
                )
            elif status == "valid" and metadata is not None:
                raw_type = metadata.get("type")
                if "type" not in metadata or (
                    isinstance(raw_type, str) and not raw_type.strip()
                ):
                    errors.append(
                        error(
                            "missing_type",
                            relpath,
                            "Concept document frontmatter requires a non-empty type.",
                        )
                    )
                elif not isinstance(raw_type, str):
                    errors.append(
                        error(
                            "invalid_type",
                            relpath,
                            "Frontmatter type must be a string.",
                        )
                    )
                for key in ("title", "description"):
                    if not metadata_value(metadata, key):
                        warnings.append(
                            warning(
                                "missing_recommended_key",
                                relpath,
                                f"Concept document is missing recommended frontmatter key: {key}.",
                            )
                        )

        if path.parent == bundle and len(text.splitlines()) > 500:
            errors.append(
                error(
                    "root_doc_too_long",
                    relpath,
                    "Root-level documentation files must not exceed 500 lines.",
                )
            )

        if path.name == "log.md":
            log_dates: list[datetime.date] = []
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.startswith("## "):
                    continue
                if not re.fullmatch(r"## \d{4}-\d{2}-\d{2}", line):
                    errors.append(
                        error(
                            "invalid_log_heading",
                            relpath,
                            f"Line {line_number} must use an ISO date heading.",
                        )
                    )
                    continue
                try:
                    log_dates.append(datetime.date.fromisoformat(line[3:]))
                except ValueError:
                    errors.append(
                        error(
                            "invalid_log_heading",
                            relpath,
                            f"Line {line_number} must use an ISO date heading.",
                        )
                    )
            if any(
                older_or_equal <= newer
                for older_or_equal, newer in zip(log_dates, log_dates[1:])
            ):
                warnings.append(
                    warning(
                        "log_order",
                        relpath,
                        "Log date headings should be newest first.",
                    )
                )

        for target in broken_links(root, bundle, path):
            warnings.append(
                warning(
                    "broken_link",
                    relpath,
                    f"Relative link target does not exist: {target}",
                )
            )

    for directory in directories_requiring_indexes(bundle):
        index_path = directory / "index.md"
        if not index_path.is_file() or index_path.is_symlink():
            errors.append(
                error(
                    "missing_index",
                    relative_path(index_path, root),
                    "Documentation directories containing Markdown files require index.md.",
                )
            )

    changes, _, malformed = index_changes(root, bundle, bundle_relative)
    for path, _ in changes:
        errors.append(
            error(
                "index_drift",
                relative_path(path, root),
                "Generated documentation index is out of date.",
            )
        )
    for path in malformed:
        errors.append(
            error(
                "malformed_markers",
                path,
                "Generated marker block is missing, duplicated, or out of order.",
            )
        )

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    warnings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    result = {
        "errors": errors,
        "mode": "check",
        "summary": {
            "concept_documents": concept_count,
            "errors": len(errors),
            "ignored_directories": sorted(
                path.relative_to(bundle).as_posix() for path in ignored_directories
            ),
            "markdown_files": len(markdown_files),
            "warnings": len(warnings),
        },
        "warnings": warnings,
    }
    return result, int(bool(errors))


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--bundle", default="docs", help="docs bundle relative to root")


def add_check_write_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", dest="action", action="store_const", const="check")
    group.add_argument("--write", dest="action", action="store_const", const="write")
    parser.set_defaults(action="check")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate an OKF docs bundle."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser("scaffold")
    add_common_arguments(scaffold_parser)
    scaffold_parser.add_argument("--default-date", default="1970-01-01")

    headers_parser = subparsers.add_parser("headers")
    add_common_arguments(headers_parser)
    add_check_write_arguments(headers_parser)
    headers_parser.add_argument("--default-date", default="1970-01-01")

    index_parser = subparsers.add_parser("index")
    add_common_arguments(index_parser)
    add_check_write_arguments(index_parser)

    check_parser = subparsers.add_parser("check")
    add_common_arguments(check_parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if args.command == "scaffold":
        root.mkdir(parents=True, exist_ok=True)
    elif not root.exists():
        print(
            json.dumps({"error": f"root not found: {root}"}, indent=2, sort_keys=True)
        )
        return 2

    try:
        bundle, bundle_relative = resolve_bundle(root, args.bundle)
    except ValueError as error_message:
        print(json.dumps({"error": str(error_message)}, indent=2, sort_keys=True))
        return 2

    if args.command != "scaffold" and not bundle.is_dir():
        print(
            json.dumps(
                {"error": f"bundle not found: {bundle_relative}"},
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    if args.command == "scaffold":
        result, status = scaffold_command(
            root, bundle, bundle_relative, args.default_date
        )
    elif args.command == "headers":
        result, status = headers_command(root, bundle, args.action, args.default_date)
    elif args.command == "index":
        result, status = index_command(root, bundle, bundle_relative, args.action)
    else:
        result, status = check_command(root, bundle, bundle_relative)
    print(json.dumps(result, indent=2, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())

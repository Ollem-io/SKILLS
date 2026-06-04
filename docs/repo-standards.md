# Repo Standards

## Skills

- Every skill conforms to the
  [Agent Skills standard](references/agent-skills-standard.md), which owns the
  `SKILL.md` frontmatter contract (`name`, `description`, `license`,
  `compatibility`, `metadata`, `allowed-tools` and their limits).
- Follow [Skill authoring](skill-authoring/index.md) for instruction patterns,
  script design, descriptions, and evaluation.
- The full upstream `skills-ref` validator is the authoritative gate: CI runs
  `just validate-skill-spec` (pinned by commit in the `Justfile`) over every
  skill, covering NFKC-normalized unicode names, `allowed-tools`/`metadata`
  typing, and the complete frontmatter contract.
- `scripts/validate_skill_names.py` is a fast, dependency-light subset for
  pre-commit and quick local feedback: allowed-field whitelist, `name` (ASCII
  subset, <= 64 chars, matches the directory), `description` (non-empty,
  <= 1024 chars), and `compatibility` (<= 500 chars). It intentionally does not
  cover unicode names or full `metadata`/`allowed-tools` typing — the upstream
  validator does, so those gaps are closed in CI rather than duplicated here.

## Repository Layout

- `AGENTS.md` is the short map for agents.
- `docs/index.md` is the full documentation table of contents.
- `project.md` contains the product or repository specification.
- Target-specific folders must follow [Structure Guide](structure-guide.md).

## Documentation

- Documentation must flow `docs/` -> topic file -> topic folder when needed.
- Any `.md` file directly under `docs/` must stay at or below 500 lines.
- If a root `docs/*.md` topic grows too large, create a folder with the same
  base name and move detailed content there.
- Every specialized documentation folder must include an `index.md`.
- Update `AGENTS.md` and `docs/index.md` in the same change as new entrypoints.

## Tooling

- Prefer repo-local task runners over chat-only instructions.
- Use `just` for repeatable commands when available.
- Use `mise` for tool installation and task encapsulation when available.
- Follow all configured pre-commit validations.
- Install `prek` hooks before committing. The configured hook types are
  `pre-commit` and `commit-msg`; the commit-message hook runs `cog verify` to
  enforce Conventional Commits locally.
- Lint Markdown with `markdownlint-cli2` (config in `.markdownlint-cli2.jsonc`);
  run via `just lint-md`. It is part of both the pre-commit and full validation
  groups.

## Language Standards

| Language | Package manager | Type checker | Linter |
| --- | --- | --- | --- |
| Python | `uv` | `ty` | `ruff` |
| TypeScript | `vp` | `vp` (`tsgo`) | `vp` (`oxlint`) |
| Markdown | — | — | `markdownlint-cli2` |

## Scripts And Tests

- Scripts must be deterministic for the same input.
- Scripts with side effects must be safe to run repeatedly.
- Every helper script should have a test.
- Expose the narrowest useful validation command for each target folder.

## Commits

- Use Conventional Commit messages: `type(scope): description`.
- Pull request titles must follow the same Conventional Commit format because
  release commits are squash-merged from the PR title.
- Keep descriptions concise, lowercase, and without a trailing period.

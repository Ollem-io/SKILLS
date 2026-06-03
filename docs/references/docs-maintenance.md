# Docs Maintenance

This file explains which documentation file owns each kind of repository
context and how agents should keep indexes current.

## File Ownership

- `AGENTS.md` is the short agent entrypoint. It links to the most important
  docs and target folders.
- `project.md` owns the product or repository specification.
- `docs/index.md` is the documentation table of contents.
- `docs/architecture.md` owns system shape, boundaries, and runtime surfaces.
- `docs/structure-guide.md` owns target folder contracts.
- `docs/repo-standards.md` owns repository-wide rules.
- `docs/skill-authoring/index.md` owns guidance for writing spec-conformant
  skills (instruction patterns, script design, descriptions, evaluation).
- `docs/local-development.md` owns setup and local validation commands.
- `docs/testing.md` owns test strategy and required validation commands.
- `docs/validation-loop.md` owns the validation-first work loop.
- `docs/observability.md` owns logs, metrics, tracing, and evidence guidance.
- `docs/security.md` owns tool policy, data handling, secrets, and trust
  boundaries.
- `docs/reliability.md` owns idempotency, durability, and operational posture.
- `docs/release-process.md` owns branch, PR, CI, and merge expectations.
- `docs/pr-review-workflow.md` owns review process and second-pass checks.
- `docs/merge-policy.md` owns PR size, fast-follow, rollback, and merge rules.
- `docs/cleanup-workflow.md` owns recurring maintenance checks.
- `docs/engineering-maintenance.md` owns agent-maintained engineering assets.
- `docs/decisions/index.md` indexes durable decision records.
- `docs/exec-plans/index.md` indexes complex resumable work plans.
- `docs/references/` contains detailed supporting material.
- `docs/references/agent-skills-standard.md` is the primary reference for the
  `SKILL.md` format; defer to the upstream Agent Skills spec it links.
- `docs/references/entrypoint-readme-template.md` is the reusable template for
  component, app, site, worker, package, or custom entrypoint readmes.

## Update Rules

- Update `AGENTS.md` when adding, moving, renaming, or removing a major
  repo entrypoint, target folder, app, site, or workflow.
- Update `docs/index.md` when adding, moving, renaming, or removing docs.
- Update `docs/references/index.md` when adding reference files.
- Keep root `docs/*.md` files short. If a topic grows too large, split it into
  `docs/<topic>/index.md` plus supporting files.
- Every specialized docs folder must have an `index.md`.
- New placeholder files must be replaced with real content before the related
  workflow is considered complete.

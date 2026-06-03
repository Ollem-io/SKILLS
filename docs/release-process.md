# Release Process

Skills become available to consumers as soon as they land on `main`: there is no
separate build or publish step. [skills.sh](references/skills-sh.md) installs
skills directly from the `main` branch. The gate is the pull request.

## Adding Or Changing A Skill

A new or changed skill must include, under `skills/<skill-name>/`:

- `SKILL.md` with valid frontmatter — `name` (matches the folder),
  `description` (what it does **and** when to use it), and `compatibility`
  (environment, required tools, network needs). See the
  [Agent Skills standard](references/agent-skills-standard.md) and
  [Skill authoring](skill-authoring/index.md).
- A `Justfile` exposing a `test` recipe.
- Deterministic helper scripts in `scripts/` (same input → same output, safe to
  re-run), each with a test in `tests/`.
- Documentation updates in the **same** change: link the skill from
  `AGENTS.md`, `docs/index.md`, `readme.md`, and `project.md`, and add it to a
  group in `skills.sh.json`.

## Pull Request Flow

1. Branch from `main` and make the change. Keep PRs small enough to review.
2. Use Conventional Commit titles: `type(scope): description`.
3. Run validation locally and include the commands and results in the PR notes:
   - `just validate` — full repository gate (also runs in CI).
   - `just validate-skill-spec` — upstream Agent Skills reference validator.
   - `just test` — script and skill tests.
4. Open a PR to `main` and fill in the PR template
   (`.github/PULL_REQUEST_TEMPLATE.md`). Link follow-up issues for any deferred
   work instead of hiding known gaps.
5. **Merge requires** all CI checks to pass **and** approval from at least one
   maintainer.
6. On merge to `main`, the skill is available via `npx skills add Ollem-io/SKILLS`.

## After Merge (skills.sh)

- Discovery and the security audit are triggered automatically by the first
  `npx skills add` install — there is no submission step.
- Audit results are visible at
  `GET https://skills.sh/api/v1/skills/audit/Ollem-io/SKILLS/<skill>` (returns
  404 until the first install). Review them; address any non-`NONE` risk levels.
- Once the skill is discovered, add the skills.sh install-count badge to
  `readme.md`.

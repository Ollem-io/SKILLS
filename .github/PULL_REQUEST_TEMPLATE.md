## Summary

<!-- What does this PR change, and why? 1-3 sentences. -->

## Type of change

<!-- The PR title should use the matching Conventional Commit type. -->

- [ ] `feat` — new skill or capability
- [ ] `fix` — bug fix
- [ ] `docs` — documentation only
- [ ] `chore` / `ci` / `refactor` / `test` — tooling, pipeline, or internal change

## Related issues

<!-- e.g. "Closes #123", or "none". Link follow-up issues for any deferred work. -->

## Changes

<!-- Bullet the notable changes. -->

-

## Skill changes

<!-- Complete if this PR adds or changes a skill under skills/<skill-name>/. Otherwise write "n/a". -->

- [ ] `SKILL.md` frontmatter is valid (`name` matches the folder; `description`
      states what it does **and** when to use it; `compatibility` declares
      tools, environment, and network needs)
- [ ] `Justfile` exposes `test`, plus `fmt`/`lint`/`check` for the script runtime
- [ ] Helper scripts are deterministic and each has a test
- [ ] Entrypoint linked from `AGENTS.md`, `docs/index.md`, `readme.md`, and
      `project.md`
- [ ] Skill added to a group in `skills.sh.json`

## Validation

<!-- Paste the commands you ran and their results (or a short summary). -->

- [ ] `just validate` — full gate (also runs in CI)
- [ ] `just validate-skill-spec` — upstream Agent Skills reference validator
- [ ] `just test` — script and skill tests

```text
<paste output or summary here>
```

## Checklist

- [ ] Title uses a Conventional Commit type: `type(scope): description`
- [ ] CI is green and the PR is ready for one maintainer approval
- [ ] Documentation updated in the same change, with no stale links

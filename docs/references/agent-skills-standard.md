# Agent Skills Standard (Primary Reference)

The [Agent Skills](https://agentskills.io) open standard is the **authoritative
reference** for the `SKILL.md` format used in this repository. Every skill under
`skills/<skill-name>/` must conform to it.

- Spec site: <https://agentskills.io/specification>
- Repository: <https://github.com/agentskills/agentskills>
- Reference validator: `skills-ref` (Python package in the repo above)
- Pinned at commit `5d4c1fd` (2026-05-20) when this reference was written.

When the spec and any local doc disagree, the spec wins; update the local doc.

## SKILL.md Frontmatter Contract

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | Yes | 1-64 chars. Unicode lowercase alphanumeric + hyphens. No leading/trailing hyphen. No consecutive `--`. Must equal the parent directory name. |
| `description` | Yes | Max 1024 chars, non-empty. States what the skill does **and when to use it**. |
| `license` | No | License name or reference to a bundled license file. |
| `compatibility` | No | Max 500 chars. Environment requirements (product, system packages, network access). |
| `metadata` | No | Arbitrary key-value mapping. Reference model types values as strings (`dict[str, str]`); prefer flat string values for portability. |
| `allowed-tools` | No | **Space-separated** string of pre-approved tools (experimental). |

Only those six top-level frontmatter fields are allowed; the reference validator
rejects unknown keys.

## Progressive Disclosure

Skills load in three stages, so authoring must respect each budget:

1. **Discovery** — only `name` + `description` (~100 tokens) load at startup.
2. **Activation** — the full `SKILL.md` body loads when a task matches.
3. **Execution** — bundled `scripts/`, `references/`, `assets/` load on demand.

Keep the `SKILL.md` body under ~500 lines / ~5000 tokens; push detail into
`references/` files the agent opens only when needed.

## Authoring Guidance (from the spec's skill-creation guides)

- **Descriptions are imperative and trigger-rich.** Write "Use when…" and name
  the concrete situations, keywords, and file types that should activate it.
- **Procedures over declarations.** Teach how to approach a class of problems,
  not a canned answer for one instance.
- **Default, don't menu.** When several approaches work, pick one default and
  mention alternatives briefly.
- **Gotchas sections** capture project-specific corrections (naming mismatches,
  soft deletes, required filters) that the agent cannot infer.
- **Templates and checklists** beat prose when output format or multi-step
  ordering matters.
- **Scripts** are for deterministic, repeatable work: no interactive prompts,
  document `--help`, emit structured output (JSON/CSV) on stdout and
  diagnostics on stderr, be idempotent, and use meaningful exit codes.
- **Evaluate descriptions** with should-trigger / should-not-trigger query sets
  before shipping; near-miss negatives catch over-triggering.

## Validation

The official `skills-ref validate <path>` enforces the frontmatter contract
above. CI runs it over every skill via `just validate-skill-spec` (pinned to a
specific upstream commit), so the full standard — including NFKC-normalized
unicode names and `metadata` value typing — is enforced. Our local
`scripts/validate_skill_names.py` is a fast, dependency-light subset for quick
feedback and pre-commit; see [Repo standards](../repo-standards.md) for the
exact split.

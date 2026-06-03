# skills.sh (Distribution & Discovery Reference)

[skills.sh](https://www.skills.sh/docs) is a Vercel-operated **distribution,
discovery, and trust layer** for agent skills. It is complementary to the
[Agent Skills standard](agent-skills-standard.md): the standard owns the
`SKILL.md` format, while skills.sh owns installation, ranking, security audits,
and a public catalog.

- Docs home: <https://www.skills.sh/docs>
- CLI: <https://www.skills.sh/docs/cli>
- API: <https://www.skills.sh/docs/api>
- FAQ: <https://www.skills.sh/docs/faq>
- Repo-page customization: <https://www.skills.sh/docs/customize>
- Audits: <https://www.skills.sh/audits>
- Captured 2026-06-03. When skills.sh and this doc disagree, the live site wins;
  update this doc.

## How It Relates To This Repo

This repository authors skills against the agentskills.io standard. skills.sh
does **not** define a new file format — it installs skills straight from a
GitHub repository's `skills/<skill-name>/` folders. That means a standards-clean
repo is already publishable: no extra build or manifest is required, only a
GitHub remote and at least one install.

## Installation Model

- Users install with `npx skills add <owner>/<skill-name>` (runs without a
  global install). It resolves the skill from the named GitHub repo, downloads
  its files, and configures the local agent.
- Skills become discoverable on the leaderboard **automatically** once the CLI
  has installed them at least once; there is no submission or publish step.
- Compatibility is per-skill and advertised via the `compatibility` frontmatter
  field. skills.sh lists support across Claude Code, Cursor, Codex, GitHub
  Copilot, Windsurf, Gemini, Cline, AMP, Antigravity, and others.

## Telemetry

- The CLI sends anonymous, aggregate install counts only (skill name, file
  list, timestamp) — no personal or device data. Counts drive leaderboard rank.
- Opt out with `DISABLE_TELEMETRY=1`.

## Security Audits

skills.sh runs automated audits after a skill's first install and surfaces a
combined risk level (NONE/LOW/MEDIUM/HIGH/CRITICAL) per provider — currently
Gen Agent Trust Hub, Socket, Snyk, Runlayer, and ZeroLeaks. Authors cannot
opt out, so treat the audit surface as part of the release contract:

- Keep helper scripts free of network calls, credential reads, and shell-outs
  the `SKILL.md` does not justify; audits flag undeclared side effects.
- Declare environment and network needs in `compatibility` so audits and users
  see them up front. See [Security](../security.md).
- Audit results are queryable at `GET /api/v1/skills/audit/{source}/{skill}`
  (404 until the first install triggers an audit).

## Repository-Page Customization (`skills.sh.json`)

An optional `skills.sh.json` at the repo root groups skills into labelled
sections on the skills.sh repo page (it does **not** affect the agent runtime):

- `$schema` (optional): JSON Schema URL for editor validation.
- `groupings` (required): array of `{ title, description?, skills: [...] }`.
- `notGrouped`: `"top"` or `"bottom"` placement for ungrouped skills.
- Limits: first 50 groups and 500 skills/group are processed; invalid groups
  are skipped; the file must be valid JSON. Changes appear after the next
  telemetry detection and cache refresh.

## Public API

Base `https://skills.sh/api/v1/`, JSON, Bearer-token auth, 600 req/min:

- `GET /skills` — leaderboard (`view=all-time|trending|hot`, `page`,
  `per_page`).
- `GET /skills/search` — fuzzy (single word) / semantic (multi-word) search.
- `GET /skills/curated` — first-party "official" skills.
- `GET /skills/{source}/{skill}` — full detail, including a SHA-256 content
  hash for cache invalidation and the complete file tree.
- `GET /skills/audit/{source}/{skill}` — audit results (see above).

## Install-Count Badge

skills.sh provides a README badge format reflecting live install counts; add it
to the entrypoint README so consumers see adoption at a glance.

## Authoring Implications For This Repo

- A clean, standards-conformant `skills/<name>/` layout is the only hard
  requirement to be installable — keep skills self-contained.
- Audits reward least privilege: minimal `allowed-tools`, no undeclared
  side effects, explicit `compatibility`.
- Consider a `skills.sh.json` once the repo hosts multiple skills worth
  grouping.

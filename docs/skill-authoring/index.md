# Skill Authoring

Guidance for writing skills that conform to the
[Agent Skills standard](../references/agent-skills-standard.md). The standard is
authoritative for the `SKILL.md` format; these pages distill its skill-creation
guides into repo-local practice.

## Contents

- [Instruction patterns](patterns.md) — how to structure `SKILL.md` bodies.
- [Script design](scripts.md) — the interface contract for helper scripts.
- [Descriptions](descriptions.md) — writing and evaluating trigger text.
- [Evaluation](evaluation.md) — measuring whether a skill helps.

## Core Principles

- **Progressive disclosure.** Keep `SKILL.md` under ~500 lines / ~5000 tokens;
  push detail into `references/` files opened only when needed.
- **Procedures over declarations.** Teach how to approach a class of problems,
  not a canned answer for one instance.
- **Spend context wisely.** Do not re-explain what the agent already knows
  (HTTP, SQL, common file formats). Capture only the non-obvious.

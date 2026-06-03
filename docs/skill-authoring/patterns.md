# Instruction Patterns

Patterns for the `SKILL.md` body, from the Agent Skills best-practices guide.

## Default, Don't Menu

When several tools or approaches work, pick one default and state it plainly.
Mention alternatives in a single line if they matter. A menu of equal options
forces the agent to choose with no basis and produces inconsistent runs.

## Gotchas Sections

Capture project-specific corrections the agent cannot infer:

```markdown
## Gotchas

- The users table uses soft deletes; queries must include `WHERE deleted_at IS NULL`.
- The user identifier is `user_id` in the database, `uid` in auth, `accountId` in billing.
```

## Templates Over Prose

When output must match a format, give a concrete template, not a description of
one. Show the exact structure the agent should fill in.

## Checklists For Multi-Step Work

For ordered, skippable workflows, give an explicit checklist so the agent can
track progress and avoid dropping steps. The existing
[repository-bootstrap](../../skills/repository-bootstrap/SKILL.md) skill's
"Required Workflow" and "Definition Of Done" sections are examples.

## Validation Loops

For work the agent can check itself, prescribe a do → validate → fix → repeat
loop with the exact validation command. See
[Validation loop](../validation-loop.md).

## Plan, Validate, Execute

For batch or destructive operations, have the agent produce an intermediate
plan, validate it against the source of truth, then execute. This makes
mistakes visible before they cause damage.

# Structure Guide

This guide owns the folder contract for this custom-target repository.

## Central Folder

- `skills/` contains one self-contained Codex skill per folder.

## Entrypoint Contract

- Each skill folder must include `SKILL.md`.
- Script-backed skills should include tests for their helper scripts.
- Each skill should expose a local `Justfile` with a `test` recipe.
- Register major skill entrypoints in `AGENTS.md`.
- Document local development and validation commands in the skill or repo docs.
- Keep migration notes explicit when adopting an existing repository.

## Definition Of Done

- The entrypoint folder exists.
- The entrypoint is linked from `AGENTS.md`.
- The relevant docs describe setup, validation, and ownership.
- The narrowest useful validation command passes or the blocker is documented.

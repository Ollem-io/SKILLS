# Script Design

The interface contract for skill helper scripts, from the Agent Skills
using-scripts guide. Use scripts for deterministic, repeatable work; use
`SKILL.md` instructions for judgement-based work.

## When To Use A Script

- The task is deterministic and benefits from the same output every run.
- The logic is error-prone to do by hand (parsing, transforms, scaffolding).
- The work is verifiable and worth a test.

Prefer one-off runners that resolve their own dependencies: `uv run --script`
(Python, with inline PEP 723 deps), `npx`/`bunx`, `deno run`, `go run`. Pin
versions where reproducibility matters. See
[Repo standards](../repo-standards.md) for required runtimes and tooling.

## Interface Contract

- **No interactive prompts.** Agents run in non-interactive shells; read input
  from arguments, flags, or stdin only.
- **Document `--help`.** Briefly, with at least one example invocation.
- **Structured output.** Emit JSON/CSV/TSV on stdout; keep it parseable and
  stable for the same input.
- **Separate channels.** Data on stdout, diagnostics and progress on stderr.
- **Meaningful exit codes.** `0` success, non-zero failure; document any others.
- **Idempotent and safe to re-run.** Side effects must tolerate repeats; offer
  a `--dry-run` for anything destructive.
- **Helpful errors.** Say what went wrong, what was expected, and what to try.
- **Predictable output size.** Paginate or cap large output rather than dumping.

## Testing

Every helper script must have a test (see [Testing](../testing.md)). Mirror the
self-contained `uv run --script` + `unittest` pattern used by
`tests/test_validate_skill_names.py` and the repository-bootstrap skill tests.

# Evaluation

Measuring whether a skill actually improves agent output, from the Agent Skills
evaluating-skills guide. Evaluation is optional per skill but recommended for
any skill whose value is not obvious from its tests.

## Test Cases

Author cases by hand in `skills/<skill-name>/evals/evals.json` (the only file
you write by hand; the rest are produced during runs). Each case is a prompt
plus a human-readable expected output and verifiable assertions. See
[`skills/repository-bootstrap/evals/evals.json`](../../skills/repository-bootstrap/evals/evals.json)
for a worked example.

- Start with 2-3 cases that vary phrasing and formality; include at least one
  edge case (ambiguous target, malformed input).
- **Assertions must be programmatically verifiable and specific.** "Output is a
  valid JSON array of objects with `name` and `email` keys" beats "output looks
  reasonable". Add them after the first run, once you see what good looks like.
- Provide any input files the prompt needs under `evals/files/`.

## With / Without Comparison

Run each case twice — `with_skill` and `without_skill` — to isolate the skill's
contribution. Capture per run: outputs, timing, and token usage.

Keep run artifacts out of the skill directory: author `evals/evals.json` inside
the skill, but write run results to a sibling workspace
(`<skill-name>-workspace/`) so large outputs never bloat the published skill.

Suggested workspace layout:

```text
<skill-name>-workspace/iteration-N/
  eval-<case-id>/
    with_skill/    { outputs, timing.json, grading.json }
    without_skill/ { outputs, timing.json, grading.json }
  benchmark.json   # aggregated pass_rate / time / tokens + delta
  feedback.json    # per-case human review notes ("" means it looked fine)
```

## Grading

- Require concrete evidence for a PASS; do not give the benefit of the doubt.
- Review the assertions themselves, not only the results — weak assertions hide
  regressions.
- For holistic quality, compare outputs blind.

## The Loop

Execute → grade → aggregate → review → iterate. Aggregate mean/stddev of
pass rate, time, and tokens, then act on patterns:

- Assertions that always pass → remove (no signal).
- Always fail → fix the skill or the assertion.
- Pass only with the skill → the skill is doing real work; understand why.
- Inconsistent → tighten the instructions.

Stop after a handful of iterations or when gains plateau.

# Evaluation

Measuring whether a skill actually improves agent output, from the Agent Skills
evaluating-skills guide. Evaluation is optional per skill but recommended for
any skill whose value is not obvious from its tests.

## Test Cases

Each eval case is a prompt plus verifiable assertions about the result:

- **Assertions must be programmatically verifiable and specific.** "Output is a
  valid JSON array of objects with `name` and `email` keys" beats "output looks
  reasonable".
- Provide any input files the prompt needs.

## With / Without Comparison

Run each case twice — `with_skill` and `without_skill` — to isolate the skill's
contribution. Capture per run: outputs, timing, and token usage.

Suggested layout:

```
evals/iteration-N/<case-id>/
  with_skill/    { outputs, timing.json, grading.json }
  without_skill/ { outputs, timing.json, grading.json }
  benchmark.json   # aggregated pass_rate / time / tokens + delta
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

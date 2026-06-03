# Descriptions

The `description` is the only body text loaded at discovery time, so it decides
whether a skill triggers at all. From the Agent Skills optimizing-descriptions
guide.

## Writing

- **Imperative and trigger-rich.** State what the skill does *and when to use
  it*: "Use when the user asks to …".
- **Name the triggers.** Include the concrete situations, keywords, file types,
  and verbs that should activate the skill, even ones the user may not say
  verbatim.
- **Trigger on intent, not implementation.** Describe the user's goal, not the
  internal mechanism.
- **Stay within budget.** Max 1024 characters; aim for one or two tight
  sentences.

## Evaluating Triggering

Before shipping a description, test that it fires on the right prompts and stays
quiet otherwise:

1. Write ~20 labelled queries: 8-10 that *should* trigger and 8-10 that should
   *not*, including near-misses that are close but wrong.
2. Split roughly 60/40 into train and validation sets to avoid overfitting the
   wording to a handful of examples.
3. Run each query a few times and compute the trigger rate (fraction of runs
   that activate the skill). Pass at a threshold (e.g. 0.5).
4. Revise wording for queries that misfire and repeat. Stop when both sets pass
   or improvements plateau.

A description that triggers on near-miss negatives is too broad; one that misses
should-trigger queries is too narrow or missing keywords.

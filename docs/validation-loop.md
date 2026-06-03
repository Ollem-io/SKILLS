# Validation Loop

Use a validation-first loop for behavior changes:

1. Identify the smallest command that should fail before the change.
2. Run it and capture the relevant failure.
3. Make the smallest useful change.
4. Rerun the focused validation.
5. Run broader repo validation when the change crosses target boundaries.
6. Document blockers with exact command output and environment limits.

Docs-only changes may use link, line-count, and readback checks when no runtime
validation applies.

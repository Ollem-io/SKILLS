# Testing

## Quick Test Map

| Goal | Primary command | External services | Test path |
| --- | --- | --- | --- |
| Fast local gate | `just validate-pre-commit` | none expected | PLACE HOLDER |
| Unit behavior | `just test-unit` | none expected | PLACE HOLDER |
| Smoke behavior | `just test-smoke` | mocked or local only | PLACE HOLDER |
| Full validation | `just validate` | documented here | PLACE HOLDER |

## Policy

- Prefer deterministic tests with stable fixtures.
- Keep heavy Docker, browser, full-stack, or external-service tests out of
  commit-time hooks unless benchmark evidence supports them.
- Record validation evidence in the task or PR when behavior changes.

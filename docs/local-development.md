# Local Development

## Bootstrap

1. Install or trust the repo toolchain.
2. Install dependencies through the repo command facade.
3. Install local hooks when they are configured.

```sh
mise install
just install
prek install
```

## Validation

Use the narrowest command that proves the change:

```sh
just validate
just validate-pre-commit
```

## Target Commands

Document target-specific install, format, lint, test, smoke, and build commands
here as soon as the target exists.

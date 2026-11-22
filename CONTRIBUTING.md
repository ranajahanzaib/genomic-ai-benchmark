# Contributing

Contributions that improve correctness, reproducibility, documentation, or usability are welcome. For larger changes, open an issue first to discuss the scope.

## Development setup

Install the runtime and development dependencies as described in [Getting started](docs/getting-started.md). Run the checks before submitting changes:

```bash
.venv/bin/pytest
.venv/bin/ruff check research services/api
.venv/bin/ruff format --check research services/api
pnpm --dir apps/web run build
pnpm --dir apps/web run typecheck
pnpm --dir apps/web run lint
```

## Pull requests

- Explain the problem and the behavior changed.
- Include or update tests for behavior changes.
- Update documentation when commands, outputs, or limitations change.
- Keep scientific claims tied to data and methods that can be reproduced.
- Do not commit credentials, private data, or unlicensed sequence data.
- Describe checks that could not be run and any known limitations.

Bug reports and feature proposals can be submitted through the repository issue tracker. For security concerns, follow [SECURITY.md](.github/SECURITY.md).

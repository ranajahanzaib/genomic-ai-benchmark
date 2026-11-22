# Genomic AI Benchmark

An independent, reproducible observatory for evaluating genomic foundation models, conventional sequence baselines, biological generalization, and potential sequence overlap.

## What it includes

This project provides a runnable local research demo: a Next.js App Router shell, a FastAPI JSON API, SQLite metadata/results, a synthetic sequence fixture, a leave-one-species-out 3-mer baseline, split validation, bounded NCBI accession retrieval, and an interactive workspace. The Evo 2 adapter follows the upstream score/embedding interfaces, but real model inference has not been verified. The demo does not provide biological evidence.

## Run locally

Requires Python 3.11 or newer, Node.js 20.19 or newer with Corepack, pnpm 12.3.4, and a modern browser. Install the dependency locks once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
pnpm --dir apps/web install --frozen-lockfile
```

Start the API and web app in separate terminals:

```bash
.venv/bin/uvicorn services.api.main:app --app-dir . --host 127.0.0.1 --port 8000
pnpm --dir apps/web run dev
```

Open <http://127.0.0.1:3000>. The API uses <http://127.0.0.1:8000> and creates `data/benchmark.sqlite3` on first start. Set `GAB_DATABASE` to change the database location. To use the optional NCBI accession importer, export a contact address as `GAB_NCBI_EMAIL` before starting Uvicorn.

The UI identifies its seeded records as synthetic fixtures. “Embedding Atlas” displays a deterministic projection of simple sequence composition features, not a model embedding. Baseline metrics are computed from the fixture on request. Imported FASTA records are stored as user supplied, unlabeled records and are excluded from the fixture evaluation until a future metadata workflow assigns split and labels.

## Checks

Install Python test/lint dependencies with `.venv/bin/pip install -r requirements-dev.lock`.

```bash
.venv/bin/pytest
.venv/bin/ruff check research services/api
.venv/bin/ruff format --check research services/api
pnpm --dir apps/web run build
pnpm --dir apps/web run typecheck
pnpm --dir apps/web run lint
```

## API

- `GET /api/health`, `/api/overview`, `/api/models`, `/api/datasets`, `/api/sequences`, `/api/runs`, `/api/splits/validate`
- `POST /api/evaluate` runs the fixture-only grouped baseline.
- `POST /api/leakage` scans the loaded split-labelled records for exact, reverse-complement and containment matches.
- `POST /api/import/fasta` accepts JSON `{ "name": "...", "fasta": ">id\\nACGT" }`.
- `POST /api/import/ncbi` retrieves a single versioned accession after `GAB_NCBI_EMAIL` is configured.

## Documentation

See [getting started](docs/getting-started.md), [architecture](docs/architecture.md), [benchmark methodology](docs/benchmark-methodology.md), [leakage detection](docs/leakage-detection.md), [limitations](docs/limitations.md), and the other topic guides in `docs/`.

The fixture computations also run from the command line: `.venv/bin/python -m research.cli evaluate --output artifacts/demo-evaluation.json` (also `leakage` and `validate-split`). Each output carries a manifest with fixture digest, runtime, and result.

## Scope and limitations

This release is a local research demo. It does not provide PostgreSQL, versioned migrations, a worker queue, broad public dataset ingestion, verified model inference, genome annotations, or a broad set of scientific tasks and reports. Outputs are not biological evidence. See [limitations](docs/limitations.md) for details.

## License

MIT. See [LICENSE](LICENSE).

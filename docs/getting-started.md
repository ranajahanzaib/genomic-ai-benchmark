# Getting started

## Requirements

Python 3.11+, Node.js 20.19+ with Corepack, pnpm 12.3.4, and a modern browser. The local demo needs no GPU, model weights, or external data service.

## Start

Install dependencies with `python3 -m venv .venv && .venv/bin/pip install -r requirements.lock` and `pnpm --dir apps/web install --frozen-lockfile`. Run `.venv/bin/uvicorn services.api.main:app --app-dir . --host 127.0.0.1 --port 8000` and `pnpm --dir apps/web run dev` in separate terminals. Visit `http://127.0.0.1:3000`. On first start the API initializes SQLite and seeds the synthetic demonstration fixture. To enable NCBI retrieval, export `GAB_NCBI_EMAIL` in the API terminal before starting Uvicorn; the request uses the official EFetch service and the UI records that the sequence remains unassigned/unlabeled.

Set `GAB_DATABASE=/path/to/workspace.sqlite3` before starting the API to choose a database path. To reset demo state, stop the process and remove the selected SQLite file; this also removes locally imported records and run history.

## Demo workflow

Explore the overview; run the grouped baseline and leakage audit; inspect individual fixture records in the feature projection; import a small FASTA file in Dataset Registry. Imported records are recorded as user-supplied data and are not silently assigned biological labels or evaluation splits.

## Checks

Install test and lint dependencies with `.venv/bin/pip install -r requirements-dev.lock`, then run `.venv/bin/pytest`, `.venv/bin/ruff check research services/api`, `.venv/bin/ruff format --check research services/api`, `pnpm --dir apps/web run build`, `pnpm --dir apps/web run typecheck`, and `pnpm --dir apps/web run lint`.

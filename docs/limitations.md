# Limitations

This release is a local demonstration and has the following constraints:

- Next.js 16 App Router hosts the interactive workspace through a small shell; the visualization code remains static HTML/CSS/JavaScript rather than React components.
- Backend uses FastAPI and Pydantic with SQLite; PostgreSQL, versioned migrations, and an asynchronous job queue are not implemented.
- An Evo 2 adapter boundary uses the official score/embedding APIs and reports runtime compatibility. No model inference has been verified, and no other model adapters are included.
- The bundled dataset is synthetic. A single versioned NCBI nuccore FASTA accession can be retrieved with provenance, but broader public dataset ingestion, annotations, real taxonomy metadata, and licensing workflows are not implemented.
- The baseline is a basic 3-mer centroid classifier on eight toy records with class metrics. A species-cluster interval is intentionally not estimated because there are too few independent groups. Calibration, multiple tasks, and production-grade split validation are absent.
- Leakage checks only exact, reverse-complement, and containment overlap within this fixture/user corpus. No homology search or external pretraining corpus coverage exists.
- The plot shows deterministic sequence-composition features, not embeddings from a model. The sequence viewer has no reference assembly or annotation tracks.
- Authentication, multiuser isolation, job recovery, a formatted research report, and deployment hardening are not implemented. JSON result downloads and CLI manifests are available. FASTA request size is limited to 5 MiB.
- Automated tests cover sequence parsing, complement, baseline behavior, leakage cases, and API workflows; there are no browser or end-to-end tests yet.

Synthetic data is labeled and must not be interpreted as biological evidence. Results from this release are not suitable for scientific claims without independent data provenance, model inference, and evaluation.

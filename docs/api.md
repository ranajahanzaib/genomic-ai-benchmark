# API

The loopback JSON API is implemented in `services/api/main.py` with FastAPI. OpenAPI documentation is available at `/docs` while the local API is running.

| Method | Path                   | Purpose                                                                 |
| ------ | ---------------------- | ----------------------------------------------------------------------- |
| GET    | `/api/health`          | Process and storage status                                              |
| GET    | `/api/overview`        | Counts                                                                  |
| GET    | `/api/models`          | Model registry                                                          |
| GET    | `/api/datasets`        | Dataset registry                                                        |
| GET    | `/api/sequences`       | Demo and imported sequence records                                      |
| GET    | `/api/runs`            | Persisted runs                                                          |
| GET    | `/api/splits/validate` | Species group crossings and supported exact/containment split checks    |
| POST   | `/api/evaluate`        | Run grouped fixture baseline                                            |
| POST   | `/api/leakage`         | Scan split-labelled records                                             |
| POST   | `/api/import/fasta`    | Validate and import FASTA JSON body                                     |
| POST   | `/api/import/ncbi`     | Retrieve one versioned nucleotide accession (requires `GAB_NCBI_EMAIL`) |

The standard-library server is a local demo and lacks production-grade authentication, rate limiting, request size limits, structured logging, and deployment hardening.

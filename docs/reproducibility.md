# Reproducibility

The demonstration fixture is checked into source control and the Python code uses deterministic methods. Species-cluster bootstrap uses a fixed seed when enough held-out species exist. The standalone CLI writes a manifest containing the fixture digest, runtime version, command, and result. API run results can be downloaded as JSON. API run records do not capture source revision, environment lock, or a reusable full experiment manifest and are not publication-ready provenance.

To reproduce a run from a fresh database, start the API and invoke the same UI action or `curl -X POST http://127.0.0.1:8000/api/evaluate`. Record the repository revision and fixture digest alongside any external reporting.

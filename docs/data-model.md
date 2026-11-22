# Data model

SQLite has four tables: `models` stores a name, family, adapter status, and JSON metadata; `datasets` stores a stable ID, name, source, status, record count, and metadata JSON; `sequences` references a dataset and stores species, split, label, sequence, and SHA-256; `runs` stores kind, status, result JSON, and creation timestamp. `services/api/schema.sql` creates the schema.

The schema does not implement versioning, migrations, multitenancy, large-sequence columnar storage, retention, or dataset revision semantics. It is intended for the local demonstration, not production storage.

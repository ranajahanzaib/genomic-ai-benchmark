"""SQLite storage and fixture seeding for Genomic AI Benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("GAB_DATABASE", ROOT / "data" / "benchmark.sqlite3"))
SCHEMA = ROOT / "services" / "api" / "schema.sql"
FIXTURE = ROOT / "fixtures" / "demo.json"


@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.executescript(SCHEMA.read_text())
        if db.execute("SELECT count(*) FROM models").fetchone()[0] == 0:
            metadata = {
                "organization": "Arc Institute",
                "family": "Evo 2",
                "architecture": "StripedHyena 2",
                "parameter_count": "7B",
                "checkpoint": "evo2_7b",
                "checkpoint_revision": None,
                "checkpoint_sha256": None,
                "training_objective": "autoregressive DNA language modeling",
                "tokenization": "single-nucleotide character-level",
                "max_context_bases": 1000000,
                "pretraining_data": "OpenGenome2 (upstream disclosure)",
                "license": None,
                "metadata_sources": ["https://github.com/ArcInstitute/evo2"],
                "adapter_implemented": True,
                "inference_verified": False,
                "unknown_fields": ["checkpoint revision and digest", "model-weight license terms"],
            }
            db.execute(
                "INSERT INTO models(name,family,status,metadata_json) VALUES(?,?,?,?)",
                (
                    "Evo 2 · 7B",
                    "Genomic language model",
                    "adapter implemented · runtime unavailable",
                    json.dumps(metadata),
                ),
            )
        if db.execute("SELECT count(*) FROM datasets").fetchone()[0] == 0:
            data = json.loads(FIXTURE.read_text())
            db.execute(
                "INSERT INTO datasets(id,name,source,status,record_count,metadata_json) VALUES(?,?,?,?,?,?)",
                (
                    data["id"],
                    data["name"],
                    data["source"],
                    "synthetic fixture",
                    len(data["samples"]),
                    json.dumps({"data_status": "synthetic fixture", "description": data["description"]}),
                ),
            )
            for sample in data["samples"]:
                digest = hashlib.sha256(sample["sequence"].encode()).hexdigest()
                db.execute(
                    "INSERT INTO sequences(id,dataset_id,species,split,label,sequence,sha256) VALUES(?,?,?,?,?,?,?)",
                    (
                        sample["id"],
                        data["id"],
                        sample["species"],
                        sample["split"],
                        sample["label"],
                        sample["sequence"],
                        digest,
                    ),
                )

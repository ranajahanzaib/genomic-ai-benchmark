"""FastAPI application exposing the local benchmark and dataset workflows."""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from starlette.responses import JSONResponse

from research.genomics import evaluate, leakage, parse_fasta, validate_split
from research.models.evo2 import Evo2Adapter

from .app import connect, initialize
from .providers.ncbi import fetch_nucleotide_fasta


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(
    title="Genomic AI Benchmark API",
    version="0.1.0",
    lifespan=lifespan,
    description="Local research demo API. Fixture computations are synthetic and are not biological evidence.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class FastaImport(BaseModel):
    name: str = Field(default="Imported FASTA", min_length=1, max_length=200)
    fasta: str = Field(min_length=1, max_length=5 * 1024 * 1024)


class NCBIImport(BaseModel):
    accession: str = Field(min_length=3, max_length=32)

    @field_validator("accession")
    @classmethod
    def normalize_versioned_accession(cls, value: str):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{1,6}_?\d+\.\d+", normalized):
            raise ValueError("Provide a versioned NCBI nucleotide accession such as NC_000913.3")
        return normalized


@app.middleware("http")
async def cap_request_body(request: Request, call_next):
    try:
        content_length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return JSONResponse({"detail": "Invalid Content-Length header"}, status_code=400)
    if content_length > 5 * 1024 * 1024:
        return JSONResponse({"detail": "Request body exceeds the 5 MiB local demo limit"}, status_code=413)
    return await call_next(request)


@app.get("/api/health")
def health():
    return {"status": "ok", "storage": "sqlite", "data_status": "synthetic fixture"}


@app.get("/api/overview")
def overview():
    with connect() as db:
        return {
            "models": db.execute("select count(*) from models").fetchone()[0],
            "datasets": db.execute("select count(*) from datasets").fetchone()[0],
            "sequences": db.execute("select count(*) from sequences").fetchone()[0],
            "runs": db.execute("select count(*) from runs").fetchone()[0],
            "data_status": "synthetic fixture",
        }


@app.get("/api/models")
def models():
    with connect() as db:
        return [dict(r) for r in db.execute("select * from models")]


@app.get("/api/models/evo2/status")
def evo2_status():
    return asdict(Evo2Adapter().status())


@app.get("/api/datasets")
def datasets():
    with connect() as db:
        return [dict(r) for r in db.execute("select id,name,source,status,record_count,metadata_json from datasets")]


@app.get("/api/sequences")
def sequences():
    with connect() as db:
        return [dict(r) for r in db.execute("select id,dataset_id,species,split,label,sequence from sequences")]


@app.get("/api/runs")
def runs():
    with connect() as db:
        return [dict(r) for r in db.execute("select * from runs order by created_at desc")]


@app.get("/api/splits/validate")
def split_validation():
    with connect() as db:
        samples = [dict(r) for r in db.execute("select id,species,split,label,sequence from sequences")]
    return validate_split(samples)


@app.post("/api/import/fasta", status_code=status.HTTP_201_CREATED)
def import_fasta(payload: FastaImport):
    try:
        records = parse_fasta(payload.fasta)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    digest = hashlib.sha256(payload.fasta.encode()).hexdigest()
    dataset_id = digest[:12]
    with connect() as db:
        db.execute(
            "insert or ignore into datasets(id,name,source,status,record_count,metadata_json) values(?,?,?,?,?,?)",
            (
                dataset_id,
                payload.name,
                "user upload",
                "local import",
                len(records),
                json.dumps({"data_status": "user supplied", "checksum": digest}),
            ),
        )
        for index, (name, seq) in enumerate(records):
            record_id = f"{dataset_id}:{index}:{name}"
            db.execute(
                "insert or ignore into sequences(id,dataset_id,species,split,label,sequence,sha256) values(?,?,?,?,?,?,?)",
                (
                    record_id,
                    dataset_id,
                    "unknown",
                    "unassigned",
                    "unlabeled",
                    seq,
                    hashlib.sha256(seq.encode()).hexdigest(),
                ),
            )
    return {"dataset_id": dataset_id, "records": len(records), "status": "imported", "data_status": "user supplied"}


@app.post("/api/import/ncbi", status_code=status.HTTP_201_CREATED)
def import_ncbi(payload: NCBIImport):
    email = os.environ.get("GAB_NCBI_EMAIL", "")
    if not email or "@" not in email or len(email) > 254:
        raise HTTPException(
            status_code=503, detail="Set GAB_NCBI_EMAIL in the API environment to enable NCBI retrieval"
        )
    try:
        fasta, record_name, sequence = fetch_nucleotide_fasta(payload.accession, email)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    accession = payload.accession
    digest = hashlib.sha256(fasta.encode()).hexdigest()
    dataset_id = f"ncbi-{accession.replace('.', '-')}"
    metadata = {
        "data_status": "retrieved public record",
        "provider": "NCBI Nucleotide EFetch",
        "accession_version": accession,
        "record_name": record_name,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "fasta_sha256": digest,
        "source_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
    }
    with connect() as db:
        db.execute(
            "insert or ignore into datasets(id,name,source,status,record_count,metadata_json) values(?,?,?,?,?,?)",
            (
                dataset_id,
                f"NCBI {accession}",
                "NCBI nuccore EFetch",
                "retrieved public record",
                1,
                json.dumps(metadata),
            ),
        )
        db.execute(
            "insert or ignore into sequences(id,dataset_id,species,split,label,sequence,sha256) values(?,?,?,?,?,?,?)",
            (
                f"{dataset_id}:0:{record_name}",
                dataset_id,
                "unknown",
                "unassigned",
                "unlabeled",
                sequence,
                hashlib.sha256(sequence.encode()).hexdigest(),
            ),
        )
    return {
        "dataset_id": dataset_id,
        "accession_version": accession,
        "records": 1,
        "status": "imported",
        "data_status": "retrieved public record",
        "fasta_sha256": digest,
    }


def persist_run(kind: str):
    with connect() as db:
        samples = [
            dict(r)
            for r in db.execute("select id,species,split,label,sequence from sequences where split != 'unassigned'")
        ]
        result = evaluate(samples) if kind == "grouped-baseline" else leakage(samples)
        cursor = db.execute(
            "insert into runs(kind,status,result_json) values(?,?,?)", (kind, result["status"], json.dumps(result))
        )
        result["run_id"] = cursor.lastrowid
        return result


@app.post("/api/evaluate", status_code=status.HTTP_201_CREATED)
def run_evaluation():
    return persist_run("grouped-baseline")


@app.post("/api/leakage", status_code=status.HTTP_201_CREATED)
def run_leakage():
    return persist_run("leakage-audit")

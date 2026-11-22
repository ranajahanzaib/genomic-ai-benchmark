"""Bounded single-record NCBI EFetch provider for versioned nucleotide accessions."""

from __future__ import annotations

import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.genomics import parse_fasta

ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MAX_BYTES = 5 * 1024 * 1024
_ACCESSION = re.compile(r"^[A-Z]{1,6}_?\d+\.\d+$")
_request_lock = threading.Lock()
_last_request_at = 0.0


def fetch_nucleotide_fasta(accession: str, email: str):
    global _last_request_at
    accession = accession.strip().upper()
    if not _ACCESSION.fullmatch(accession):
        raise ValueError("Provide a versioned NCBI nucleotide accession such as NC_000913.3")
    if not email or "@" not in email or len(email) > 254:
        raise ValueError("Set GAB_NCBI_EMAIL to a contact email before using NCBI retrieval")
    params = urlencode(
        {
            "db": "nuccore",
            "id": accession,
            "rettype": "fasta",
            "retmode": "text",
            "tool": "genomic_ai_benchmark",
            "email": email,
        }
    )
    request = Request(
        f"{ENDPOINT}?{params}", headers={"User-Agent": f"GenomicAIBenchmark/0.1 ({email})", "Accept": "text/plain"}
    )
    try:
        # Keep this process below NCBI's recommended unauthenticated request rate.
        with _request_lock:
            delay = 0.34 - (time.monotonic() - _last_request_at)
            if delay > 0:
                time.sleep(delay)
            _last_request_at = time.monotonic()
            with urlopen(request, timeout=20) as response:
                raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"NCBI EFetch request failed: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise RuntimeError("NCBI response exceeds the 5 MiB local import limit")
    try:
        fasta = raw.decode("utf-8", errors="strict")
        records = parse_fasta(fasta)
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError(f"NCBI returned an invalid FASTA record: {exc}") from exc
    if len(records) != 1:
        raise RuntimeError(f"Expected one FASTA record for {accession}, received {len(records)}")
    returned_accession = records[0][0].split()[0]
    if returned_accession != accession:
        raise RuntimeError(
            f"NCBI returned {returned_accession!r}, which does not match requested accession {accession}"
        )
    return fasta, records[0][0], records[0][1]

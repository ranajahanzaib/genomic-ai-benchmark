# Data sources

The bundled records in `fixtures/demo.json` are generated toy sequences for exercising UI and evaluation paths. They are not sourced from an organism, assembly, publication, or public archive. Their labels are illustrative and synthetic.

The API can retrieve a single versioned nucleotide accession from NCBI nuccore through the official EFetch endpoint. The request is limited to one FASTA record and 5 MiB, requires `GAB_NCBI_EMAIL`, records the exact accession version, retrieval timestamp, source endpoint, and FASTA SHA-256, and keeps the imported sequence unlabeled with unassigned split. The provider limits requests to less than three per second per process. NCBI's documented EFetch API supports FASTA retrieval by accession; the application follows its request identity guidance and conservative rate recommendation. [NCBI EFetch quick start](https://www.ncbi.nlm.nih.gov/books/NBK25500/), [E-utilities usage guidelines](https://www.ncbi.nlm.nih.gov/books/NBK25499/).

NCBI provides a public retrieval mechanism, but this feature does not infer taxonomic labels or genome assembly context. Users should verify the record's provenance and applicable record terms before analysis or redistribution. Large-scale retrieval, annotation packages, GTDB, and OpenGenome2 ingestion are not implemented.

FASTA import accepts user-provided records containing A, C, G, T, or N. It records the input digest and leaves taxon, split, and label as unknown/unassigned. Users remain responsible for source, license, accession, build, and evidence metadata; the current form does not collect those fields yet.

# Leakage detection

The current audit compares pairs of records whose stored split labels differ and reports exact strings, reverse complements, or full containment. It scans only loaded split-labelled sequences. The overview reports this limited corpus coverage with each result.

No hits do not mean no pretraining contamination. The implementation does not detect approximate homology, local alignment, shared accessions, common motifs, or exposure through unknown corpora. A homology or contamination claim requires indexed corpus coverage, tool/version parameters, thresholds, provenance, and inspectable alignment evidence.

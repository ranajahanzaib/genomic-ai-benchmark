# Splitting and generalization

The demonstration uses leave-one-species-out folds in its baseline. This is taxon-grouped toy evaluation; it does not establish independence from training data, taxonomy-aware homology clusters, genome builds, time, or pretraining exposure. Fixture split labels are retained for leakage scanning, while the grouped baseline constructs its own leave-one-species-out folds from the species field.

Future benchmark releases should publish split manifests, grouping keys, sequence identity thresholds, excluded records, and checksums, and verify no group crosses the split boundary.

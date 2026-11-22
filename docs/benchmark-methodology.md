# Benchmark methodology

The local example is a binary toy classification task on synthetic records. A 3-mer count vector is computed independently per sequence. For each held-out species, class centroids are arithmetic means of training vectors, and the held-out sample is assigned the label with the smallest squared Euclidean distance. Accuracy is the fraction of evaluated predictions equal to fixture labels. Folds lacking both training labels are excluded and listed.

This toy example has eight generated records and very few species; it is not a benchmark result. A species-cluster bootstrap interval is not estimated when fewer than ten held-out species are available, because per-record intervals would incorrectly imply independent observations. There is no hyperparameter tuning, calibration, or real biological evidence. These results must not be compared with foundation model scores.

"""Small deterministic sequence methods used in the local demonstration."""

from __future__ import annotations

import random
from collections import Counter


def complement(seq: str) -> str:
    return seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def parse_fasta(text: str):
    records, name, pieces = [], None, []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if name is not None:
                records.append((name, "".join(pieces)))
            name, pieces = line[1:].strip(), []
            if not name:
                raise ValueError(f"FASTA header is empty on line {line_no}")
        else:
            if name is None:
                raise ValueError(f"Sequence data precedes first FASTA header on line {line_no}")
            seq = "".join(line.split()).upper()
            invalid = set(seq) - set("ACGTN")
            if invalid:
                raise ValueError(f"Invalid nucleotide symbol(s) on line {line_no}: {''.join(sorted(invalid))}")
            pieces.append(seq)
    if name is not None:
        records.append((name, "".join(pieces)))
    if not records or any(not seq for _, seq in records):
        raise ValueError("FASTA must contain at least one non-empty sequence")
    return records


def species_cluster_bootstrap_interval(predictions, replicates: int = 5000, seed: int = 27):
    """Percentile interval resampling held-out species clusters, not individual records."""
    grouped = {}
    for row in predictions:
        grouped.setdefault(row["species"], []).append(row["truth"] == row["prediction"])
    if len(grouped) < 10:
        return None
    clusters = [values for _, values in sorted(grouped.items())]
    rng = random.Random(seed)
    estimates = []
    for _ in range(replicates):
        draw = [rng.choice(clusters) for _ in clusters]
        estimates.append(sum(sum(cluster) for cluster in draw) / sum(map(len, draw)))
    estimates.sort()
    return [estimates[int(0.025 * (replicates - 1))], estimates[int(0.975 * (replicates - 1))]]


def classification_metrics(predictions):
    labels = sorted({p["truth"] for p in predictions} | {p["prediction"] for p in predictions})
    per_class = {}
    for label in labels:
        tp = sum(p["truth"] == label and p["prediction"] == label for p in predictions)
        fp = sum(p["truth"] != label and p["prediction"] == label for p in predictions)
        fn = sum(p["truth"] == label and p["prediction"] != label for p in predictions)
        support = sum(p["truth"] == label for p in predictions)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
    macro_f1 = sum(m["f1"] for m in per_class.values()) / len(per_class) if per_class else 0.0
    macro_recall = sum(m["recall"] for m in per_class.values()) / len(per_class) if per_class else 0.0
    return {"per_class": per_class, "macro_f1": macro_f1, "balanced_accuracy": macro_recall}


def evaluate(samples):
    """Grouped leave-one-species-out 3-mer nearest-centroid baseline."""
    species = sorted({s["species"] for s in samples})
    if len(species) < 2:
        return {"status": "not run", "reason": "At least two species are required for grouped evaluation."}

    def vector(seq):
        return Counter(seq[i : i + 3] for i in range(max(0, len(seq) - 2)))

    predictions, excluded = [], []
    for heldout in species:
        train = [s for s in samples if s["species"] != heldout]
        test = [s for s in samples if s["species"] == heldout]
        labels = sorted({s["label"] for s in train})
        if len(labels) < 2:
            excluded.extend(s["id"] for s in test)
            continue
        centroids = {}
        for label in labels:
            rows = [vector(s["sequence"]) for s in train if s["label"] == label]
            keys = set().union(*(r.keys() for r in rows))
            centroids[label] = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
        for sample in test:
            v = vector(sample["sequence"])
            pred = min(
                labels,
                key=lambda label: sum((v[k] - centroids[label].get(k, 0)) ** 2 for k in set(v) | set(centroids[label])),
            )
            predictions.append({"id": sample["id"], "species": heldout, "truth": sample["label"], "prediction": pred})
    if not predictions:
        return {"status": "not run", "reason": "No held-out fold had both classes in its training data."}
    correct = sum(p["truth"] == p["prediction"] for p in predictions)
    return {
        "status": "completed",
        "method": "3-mer count nearest centroid",
        "split": "leave-one-species-out",
        "n": len(predictions),
        "accuracy": correct / len(predictions),
        "accuracy_cluster_bootstrap_95": species_cluster_bootstrap_interval(predictions),
        "uncertainty_note": "Cluster bootstrap is not estimated with fewer than 10 held-out species; this fixture has too few independent groups."
        if len({p["species"] for p in predictions}) < 10
        else "Percentile interval resamples held-out species clusters.",
        **classification_metrics(predictions),
        "predictions": predictions,
        "excluded_ids": excluded,
        "data_status": "synthetic fixture",
    }


def leakage(samples):
    samples = [sample for sample in samples if sample["split"] != "unassigned"]
    hits = []
    for i, a in enumerate(samples):
        for b in samples[i + 1 :]:
            if a["split"] == b["split"]:
                continue
            x, y = a["sequence"], b["sequence"]
            kind = (
                "exact"
                if x == y
                else "reverse-complement"
                if x == complement(y)
                else "containment"
                if x in y or y in x
                else None
            )
            if kind:
                hits.append(
                    {
                        "left": a["id"],
                        "right": b["id"],
                        "kind": kind,
                        "left_split": a["split"],
                        "right_split": b["split"],
                    }
                )
    return {
        "status": "completed",
        "method": "exact, reverse-complement, and containment checks",
        "corpus_coverage": "all sequences in this synthetic dataset only",
        "hits": hits,
        "hit_count": len(hits),
        "data_status": "synthetic fixture",
    }


def validate_split(samples):
    group_splits = {}
    for sample in samples:
        if sample["split"] == "unassigned":
            continue
        group_splits.setdefault(sample["species"], set()).add(sample["split"])
    crossing = [
        {"species": group, "splits": sorted(splits)}
        for group, splits in sorted(group_splits.items())
        if len(splits) > 1
    ]
    audit = leakage([sample for sample in samples if sample["split"] != "unassigned"])
    return {
        "status": "completed",
        "strategy": "declared split labels",
        "species_crossings": crossing,
        "species_crossing_count": len(crossing),
        "exact_or_containment_cross_split_hits": audit["hits"],
        "scope": "Checks only the loaded local sequences; no homology or pretraining-corpus evidence.",
    }

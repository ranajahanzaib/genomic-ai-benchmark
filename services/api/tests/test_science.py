import json
import unittest
from pathlib import Path

from research.genomics import (
    complement,
    evaluate,
    leakage,
    parse_fasta,
    species_cluster_bootstrap_interval,
    validate_split,
)


class SequenceTests(unittest.TestCase):
    def test_fasta_multiline_and_normalization(self):
        self.assertEqual(parse_fasta(">a\nacg\ntt\n>b note\nNN"), [("a", "ACGTT"), ("b note", "NN")])

    def test_fasta_rejects_invalid_symbol(self):
        with self.assertRaisesRegex(ValueError, "Invalid nucleotide"):
            parse_fasta(">a\nACGTX")

    def test_reverse_complement(self):
        self.assertEqual(complement("AACGTN"), "NACGTT")

    def test_grouped_fixture_evaluation(self):
        fixture = json.loads((Path(__file__).resolve().parents[3] / "fixtures/demo.json").read_text())
        result = evaluate(fixture["samples"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["split"], "leave-one-species-out")
        self.assertEqual(result["n"], 8)
        self.assertTrue(0 <= result["accuracy"] <= 1)

    def test_one_species_is_not_evaluated(self):
        self.assertEqual(evaluate([{"species": "a", "sequence": "ACG", "label": "x", "id": "1"}])["status"], "not run")

    def test_uncertainty_is_not_estimated_with_too_few_species(self):
        rows = [{"species": "sp1", "truth": "a", "prediction": "a"}]
        self.assertIsNone(species_cluster_bootstrap_interval(rows))

    def test_species_cluster_bootstrap_is_deterministic(self):
        rows = [{"species": f"sp{i}", "truth": "a", "prediction": "a" if i % 2 else "b"} for i in range(12)]
        self.assertEqual(species_cluster_bootstrap_interval(rows), species_cluster_bootstrap_interval(rows))

    def test_split_validator_reports_species_crossing(self):
        samples = [
            {"id": "1", "species": "shared", "split": "train", "sequence": "AAAA", "label": "x"},
            {"id": "2", "species": "shared", "split": "test", "sequence": "CCCC", "label": "y"},
        ]
        self.assertEqual(validate_split(samples)["species_crossing_count"], 1)

    def test_cross_split_exact_match(self):
        rows = [
            {"id": "a", "split": "train", "sequence": "AACCGG", "species": "a", "label": "x"},
            {"id": "b", "split": "test", "sequence": "AACCGG", "species": "b", "label": "x"},
        ]
        out = leakage(rows)
        self.assertEqual(out["hits"][0]["kind"], "exact")

    def test_reverse_complement_and_containment(self):
        rows = [
            {"id": "a", "split": "train", "sequence": "AACCGG", "species": "a", "label": "x"},
            {"id": "b", "split": "test", "sequence": "CCGGTT", "species": "b", "label": "x"},
            {"id": "c", "split": "validation", "sequence": "TTTAACCGGAAA", "species": "c", "label": "x"},
        ]
        kinds = {h["kind"] for h in leakage(rows)["hits"]}
        self.assertIn("reverse-complement", kinds)
        self.assertIn("containment", kinds)

    def test_same_split_pair_is_not_cross_split_leakage(self):
        rows = [
            {"id": "a", "split": "train", "sequence": "AACCGG", "species": "a", "label": "x"},
            {"id": "b", "split": "train", "sequence": "AACCGG", "species": "b", "label": "x"},
        ]
        self.assertEqual(leakage(rows)["hit_count"], 0)

    def test_unassigned_samples_are_not_compared_to_split_data(self):
        rows = [
            {"id": "a", "split": "train", "sequence": "AACCGG", "species": "a", "label": "x"},
            {"id": "b", "split": "unassigned", "sequence": "AACCGG", "species": "unknown", "label": "unlabeled"},
        ]
        self.assertEqual(leakage(rows)["hit_count"], 0)

    def test_unrelated_pair_not_reported(self):
        rows = [
            {"id": "a", "split": "train", "sequence": "AAAAAAAA", "species": "a", "label": "x"},
            {"id": "b", "split": "test", "sequence": "CCCCCCCC", "species": "b", "label": "x"},
        ]
        self.assertEqual(leakage(rows)["hit_count"], 0)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.api import app as storage
from services.api.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        storage.DB = Path(self.temp.name) / "test.sqlite3"
        storage.initialize()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_health_and_real_overview_counts(self):
        self.assertEqual(self.client.get("/api/health").json()["status"], "ok")
        overview = self.client.get("/api/overview").json()
        self.assertEqual(overview["sequences"], 8)
        self.assertEqual(overview["data_status"], "synthetic fixture")

    def test_evaluation_is_persisted(self):
        result = self.client.post("/api/evaluate").json()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["n"], 8)
        self.assertTrue(result["run_id"])
        runs = self.client.get("/api/runs").json()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["kind"], "grouped-baseline")

    def test_fasta_import_is_validated_and_stays_unassigned(self):
        response = self.client.post("/api/import/fasta", json={"name": "sample", "fasta": ">same\nacgt\n>same\nTTAA"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["records"], 2)
        added = [
            r for r in self.client.get("/api/sequences").json() if r["dataset_id"] == response.json()["dataset_id"]
        ]
        self.assertEqual(len(added), 2)
        self.assertTrue(all(r["split"] == "unassigned" and r["label"] == "unlabeled" for r in added))

    def test_invalid_fasta_has_actionable_error(self):
        response = self.client.post("/api/import/fasta", json={"name": "bad", "fasta": ">seq\nACGTX"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Invalid nucleotide", response.json()["detail"])

    def test_request_size_limit(self):
        response = self.client.post(
            "/api/import/fasta", content=b" " * (5 * 1024 * 1024 + 1), headers={"content-type": "application/json"}
        )
        self.assertEqual(response.status_code, 413)

    def test_split_validation_endpoint_is_explicit(self):
        result = self.client.get("/api/splits/validate").json()
        self.assertEqual(result["species_crossing_count"], 0)
        self.assertIn("no homology", result["scope"])

    def test_evo2_status_reports_runtime_without_loading_weights(self):
        result = self.client.get("/api/models/evo2/status").json()
        self.assertEqual(result["model_id"], "evo2_7b")
        self.assertFalse(result["available"])
        self.assertEqual(result["supported_operations"], [])

    @patch.dict("os.environ", {"GAB_NCBI_EMAIL": "research@example.org"})
    @patch(
        "services.api.main.fetch_nucleotide_fasta",
        return_value=(">NC_000913.3 Escherichia coli\nACGTACGT\n", "NC_000913.3 Escherichia coli", "ACGTACGT"),
    )
    def test_ncbi_import_records_accession_and_checksum(self, fetch):
        response = self.client.post("/api/import/ncbi", json={"accession": "NC_000913.3"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["accession_version"], "NC_000913.3")
        self.assertTrue(data["fasta_sha256"])
        fetch.assert_called_once_with("NC_000913.3", "research@example.org")
        record = next(d for d in self.client.get("/api/datasets").json() if d["id"] == data["dataset_id"])
        self.assertEqual(record["source"], "NCBI nuccore EFetch")
        self.assertIn("accession_version", record["metadata_json"])

    def test_ncbi_requires_versioned_accession(self):
        response = self.client.post("/api/import/ncbi", json={"accession": "NC_000913"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("versioned NCBI nucleotide accession", str(response.json()["detail"]))

    def test_ncbi_requires_contact_configuration(self):
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.post("/api/import/ncbi", json={"accession": "NC_000913.3"})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from research.cli import run


class CliTests(unittest.TestCase):
    def test_cli_evaluate_manifest(self):
        manifest = run("evaluate")
        self.assertEqual(manifest["command"], "evaluate")
        self.assertEqual(manifest["manifest_version"], 1)
        self.assertTrue(manifest["fixture_sha256"])
        self.assertEqual(manifest["result"]["status"], "completed")
        self.assertEqual(manifest["result"]["accuracy"], 1.0)
        self.assertEqual(manifest["result"]["n"], 8)

    def test_cli_leakage_manifest(self):
        manifest = run("leakage")
        self.assertEqual(manifest["command"], "leakage")
        self.assertEqual(manifest["result"]["status"], "completed")
        self.assertEqual(manifest["result"]["hit_count"], 1)
        self.assertEqual(manifest["result"]["hits"][0]["kind"], "exact")

    def test_cli_validate_split_manifest(self):
        manifest = run("validate-split")
        self.assertEqual(manifest["command"], "validate-split")
        self.assertEqual(manifest["result"]["status"], "completed")
        self.assertEqual(manifest["result"]["species_crossing_count"], 0)

    def test_cli_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "output.json"
            manifest = run("evaluate")
            out_path.write_text(json.dumps(manifest, indent=2))
            loaded = json.loads(out_path.read_text())
            self.assertEqual(loaded["command"], "evaluate")
            self.assertEqual(loaded["result"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()

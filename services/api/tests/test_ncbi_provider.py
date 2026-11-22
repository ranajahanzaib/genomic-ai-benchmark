import io
import unittest
from unittest.mock import patch

from services.api.providers import ncbi


class NCBIProviderTests(unittest.TestCase):
    def test_fetches_one_versioned_fasta_and_sets_contact(self):
        payload = b">NC_000913.3 Escherichia coli\nACGTACGT\n"
        with (
            patch.object(ncbi.time, "monotonic", side_effect=[1000.0, 1000.0]),
            patch.object(ncbi, "urlopen", return_value=io.BytesIO(payload)) as fetch,
        ):
            fasta, name, sequence = ncbi.fetch_nucleotide_fasta("nc_000913.3", "research@example.org")
        request = fetch.call_args.args[0]
        self.assertIn("id=NC_000913.3", request.full_url)
        self.assertIn("email=research%40example.org", request.full_url)
        self.assertEqual((name, sequence), ("NC_000913.3 Escherichia coli", "ACGTACGT"))
        self.assertTrue(fasta.startswith(">NC_000913.3"))

    def test_rejects_unversioned_accession_before_network(self):
        with patch.object(ncbi, "urlopen") as fetch:
            with self.assertRaisesRegex(ValueError, "versioned"):
                ncbi.fetch_nucleotide_fasta("NC_000913", "research@example.org")
        fetch.assert_not_called()

    def test_rejects_accession_mismatch(self):
        payload = b">NC_000001.1 unexpected record\nACGT\n"
        with (
            patch.object(ncbi.time, "monotonic", side_effect=[2000.0, 2000.0]),
            patch.object(ncbi, "urlopen", return_value=io.BytesIO(payload)),
        ):
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                ncbi.fetch_nucleotide_fasta("NC_000913.3", "research@example.org")


if __name__ == "__main__":
    unittest.main()

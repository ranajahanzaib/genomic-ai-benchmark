import unittest

from research.models.base import ModelUnavailableError
from research.models.evo2 import Evo2Adapter


class FakeEvo2:
    def score_sequences(self, sequences, **kwargs):
        self.seen = (sequences, kwargs)
        return [-1.25 for _ in sequences]


class Evo2AdapterTests(unittest.TestCase):
    def test_status_never_claims_loaded_inference_without_weights(self):
        status = Evo2Adapter().status()
        self.assertEqual(status.model_id, "evo2_7b")
        self.assertFalse(status.available)
        self.assertEqual(status.supported_operations, ())
        self.assertTrue(status.reasons)

    def test_scoring_uses_upstream_operation_and_normalizes_dna(self):
        model = FakeEvo2()
        adapter = Evo2Adapter(model=model)
        self.assertEqual(adapter.score_sequences(["acgt"]), [-1.25])
        self.assertEqual(model.seen[0], ["ACGT"])
        self.assertEqual(model.seen[1]["reduce_method"], "mean")

    def test_scoring_refuses_invalid_input_and_unloaded_state(self):
        with self.assertRaisesRegex(ValueError, "unsupported DNA"):
            Evo2Adapter(model=FakeEvo2()).score_sequences(["ACGTX"])
        with self.assertRaises(ModelUnavailableError):
            Evo2Adapter().score_sequences(["ACGT"])


if __name__ == "__main__":
    unittest.main()

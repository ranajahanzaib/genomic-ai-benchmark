"""Adapter for Arc Institute's official Evo 2 inference API.

The inference methods follow the upstream ``Evo2.score_sequences`` and
``Evo2(..., return_embeddings=True)`` interfaces. The heavyweight runtime is
optional and imported only after an explicit call to ``load``.
"""

from __future__ import annotations

import importlib.util
import platform
import re
import sys

from research.models.base import AdapterStatus, ModelAdapter, ModelUnavailableError


class Evo2Adapter(ModelAdapter):
    MODEL_ID = "evo2_7b"
    MAX_CONTEXT = 1_000_000

    def __init__(self, model=None):
        self._model = model

    def status(self) -> AdapterStatus:
        reasons = []
        environment = {
            "platform": platform.system(),
            "python": platform.python_version(),
            "evo2_package": False,
            "torch_package": False,
            "cuda_available": False,
            "cuda_version": None,
            "cudnn_version": None,
        }
        version = sys.version_info[:2]
        if platform.system() != "Linux":
            reasons.append("Official local inference supports Linux or limited WSL2; this host is not Linux.")
        if version not in ((3, 11), (3, 12)):
            reasons.append("Official Evo 2 setup supports Python 3.11 or 3.12.")
        try:
            environment["evo2_package"] = importlib.util.find_spec("evo2") is not None
        except (ImportError, ValueError):
            environment["evo2_package"] = False
        try:
            environment["torch_package"] = importlib.util.find_spec("torch") is not None
        except (ImportError, ValueError):
            environment["torch_package"] = False
        if not environment["evo2_package"]:
            reasons.append("The official evo2 Python package is not installed.")
        # Avoid importing the heavyweight CUDA runtime just to render status on unsupported hosts.
        if platform.system() == "Linux" and version in ((3, 11), (3, 12)) and environment["torch_package"]:
            try:
                import torch

                environment["cuda_available"] = bool(torch.cuda.is_available())
                environment["cuda_version"] = torch.version.cuda
                environment["cudnn_version"] = torch.backends.cudnn.version()
                if torch.cuda.is_available():
                    environment["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            except Exception as exc:  # runtime/environment diagnostics must remain visible rather than break overview
                reasons.append(f"PyTorch CUDA inspection failed: {type(exc).__name__}: {exc}")
        if not environment["torch_package"]:
            reasons.append("PyTorch is not installed.")
        if not environment["cuda_available"]:
            reasons.append("A supported CUDA GPU is not available; Evo 2 does not provide CPU inference.")
        cuda_version = environment["cuda_version"]
        if cuda_version:
            match = re.match(r"(\d+)\.(\d+)", cuda_version)
            if not match or tuple(map(int, match.groups())) < (12, 1):
                reasons.append("The official setup requires CUDA 12.1 or newer.")
        cudnn = environment["cudnn_version"]
        if cudnn and cudnn < 90300:
            reasons.append("The official setup requires cuDNN 9.3 or newer.")
        if self._model is None:
            reasons.append("Model weights have not been loaded and locally validated.")
        available = not reasons and self._model is not None
        operations = ("sequence_likelihood", "embeddings") if available else ()
        return AdapterStatus(self.MODEL_ID, available, operations, tuple(reasons), environment)

    def load(self, *, local_path: str | None = None, allow_download: bool = False):
        status = self.status()
        blockers = [reason for reason in status.reasons if "Model weights have not been loaded" not in reason]
        if blockers:
            raise ModelUnavailableError("; ".join(blockers))
        if not local_path and not allow_download:
            raise ModelUnavailableError("Provide local_path or explicitly allow first-use model downloads.")
        from evo2 import Evo2

        self._model = Evo2(self.MODEL_ID, local_path=local_path)
        return self

    @classmethod
    def _validate_sequences(cls, sequences: list[str]):
        if not sequences:
            raise ValueError("At least one DNA sequence is required")
        for index, sequence in enumerate(sequences):
            sequence = sequence.upper()
            if not sequence or len(sequence) > cls.MAX_CONTEXT:
                raise ValueError(f"Sequence {index} must have between 1 and {cls.MAX_CONTEXT} bases")
            invalid = set(sequence) - set("ACGTN")
            if invalid:
                raise ValueError(f"Sequence {index} contains unsupported DNA symbols: {''.join(sorted(invalid))}")

    def score_sequences(self, sequences: list[str], *, batch_size: int = 1, average_reverse_complement: bool = False):
        self._validate_sequences(sequences)
        if self._model is None:
            raise ModelUnavailableError("Load and validate an Evo 2 checkpoint before scoring.")
        return self._model.score_sequences(
            [seq.upper() for seq in sequences],
            batch_size=batch_size,
            reduce_method="mean",
            average_reverse_complement=average_reverse_complement,
        )

    def extract_embeddings(self, sequences: list[str], *, layer_name: str = "blocks.28.mlp.l3"):
        self._validate_sequences(sequences)
        if self._model is None:
            raise ModelUnavailableError("Load and validate an Evo 2 checkpoint before extracting embeddings.")
        import torch

        vectors = []
        for sequence in sequences:
            input_ids = (
                torch.tensor(self._model.tokenizer.tokenize(sequence.upper()), dtype=torch.int)
                .unsqueeze(0)
                .to("cuda:0")
            )
            _, layers = self._model(input_ids, return_embeddings=True, layer_names=[layer_name])
            vectors.append(layers[layer_name].mean(dim=1).squeeze(0).float().cpu().tolist())
        return vectors

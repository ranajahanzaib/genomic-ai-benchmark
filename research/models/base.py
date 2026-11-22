"""Small capability contract shared by model adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ModelUnavailableError(RuntimeError):
    """Raised when an adapter cannot run in the current environment."""


@dataclass(frozen=True)
class AdapterStatus:
    model_id: str
    available: bool
    supported_operations: tuple[str, ...]
    reasons: tuple[str, ...]
    environment: dict


class ModelAdapter(ABC):
    @abstractmethod
    def status(self) -> AdapterStatus:
        """Report verified environment capabilities without loading weights."""

    @abstractmethod
    def score_sequences(self, sequences: list[str]) -> list[float]:
        """Return documented sequence scores when the integration is operational."""

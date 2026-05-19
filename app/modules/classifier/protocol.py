"""Classifier protocol — abstract interface for complaint classification.

Constitution V: Strategy pattern via ABC.
"""

from abc import ABC, abstractmethod

from app.modules.normalizer.protocol import NormalizedComplaint
from app.schemas.classification import ClassificationResult


class ClassifierProtocol(ABC):
    """Abstract base class for complaint classification strategies."""

    @abstractmethod
    async def classify(self, normalized: NormalizedComplaint) -> ClassificationResult:
        """Classify a normalized complaint into department, urgency, sentiment.

        Args:
            normalized: Output from the normalizer module.

        Returns:
            ClassificationResult with department, urgency_score, sentiment.
        """
        ...

"""Normalizer protocol — abstract interface for multilingual normalization.

Constitution V: Strategy pattern via Protocol/ABC.
Constitution II: Standalone invocation, zero FastAPI dependency.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class NormalizedComplaint(BaseModel):
    """Output of the normalization step."""

    original_text: str
    normalized_text: str
    detected_language: str
    extracted_intent: str
    extracted_entities: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class NormalizerProtocol(ABC):
    """Abstract base class for complaint normalization strategies."""

    @abstractmethod
    async def process(self, text: str, language_hint: str | None = None) -> NormalizedComplaint:
        """Normalize raw complaint text into structured intent + entities.

        Args:
            text: Raw complaint text in any supported language.
            language_hint: Optional language hint (roman_urdu, urdu, english, mixed).

        Returns:
            NormalizedComplaint with extracted intent and entities.
        """
        ...

"""Normalizer module — factory and exports."""

from app.core.config import MLStrategy, Settings
from app.modules.normalizer.llm_strategy import LLMNormalizer
from app.modules.normalizer.protocol import NormalizedComplaint, NormalizerProtocol

__all__ = ["NormalizerProtocol", "NormalizedComplaint", "create_normalizer"]


def create_normalizer(settings: Settings, http_client) -> NormalizerProtocol:
    """Factory: create normalizer based on configured strategy.

    Constitution V: Runtime selection via environment variable.
    """
    if settings.app_normalizer_strategy == MLStrategy.LLM:
        return LLMNormalizer(
            http_client=http_client,
            api_key=settings.anthropic_api_key or "",
        )
    else:
        # Fallback — LLM with empty key triggers graceful degradation
        return LLMNormalizer(
            http_client=http_client,
            api_key="",
        )

"""Classifier module — factory and exports."""

from app.core.config import MLStrategy, Settings
from app.modules.classifier.llm_strategy import LLMClassifier
from app.modules.classifier.protocol import ClassifierProtocol

__all__ = ["ClassifierProtocol", "create_classifier"]


def create_classifier(settings: Settings, http_client) -> ClassifierProtocol:
    """Factory: create classifier based on configured strategy.

    Constitution V: Runtime selection via environment variable.
    """
    if settings.app_classifier_strategy == MLStrategy.LLM:
        return LLMClassifier(
            http_client=http_client,
            api_key=settings.openrouter_api_key or "",
            model=settings.openrouter_model,
        )
    else:
        # Keyword-only mode — LLM with empty key triggers fallback
        return LLMClassifier(
            http_client=http_client,
            api_key="",
        )

"""NaqsKAR application configuration via pydantic-settings."""

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class MLStrategy(str, Enum):
    LLM = "llm"
    KEYWORD = "keyword"
    NONE = "none"


class GeoStrategy(str, Enum):
    LLM_GAZETTEER = "llm_gazetteer"
    GAZETTEER_ONLY = "gazetteer_only"
    NONE = "none"


class DedupStrategy(str, Enum):
    EMBEDDING = "embedding"
    NONE = "none"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # --- LLM Provider ---
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "z-ai/glm-4.5-air:free"
    app_llm_provider: LLMProvider = LLMProvider.OPENROUTER

    # --- Module Strategies ---
    app_normalizer_strategy: MLStrategy = MLStrategy.LLM
    app_classifier_strategy: MLStrategy = MLStrategy.LLM
    app_geo_strategy: GeoStrategy = GeoStrategy.LLM_GAZETTEER
    app_dedup_strategy: DedupStrategy = DedupStrategy.EMBEDDING

    # --- Deduplication ---
    dedup_window_days: int = 7
    dedup_radius_meters: int = 500

    # --- Ollama Fallback ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()

"""Geo-Extractor module — factory and exports."""

from typing import Optional

from app.core.config import GeoStrategy, Settings
from app.modules.geo_extractor.gazetteer import Gazetteer
from app.modules.geo_extractor.llm_strategy import LLMGeoExtractor
from app.modules.geo_extractor.protocol import GeoExtractorProtocol

__all__ = ["GeoExtractorProtocol", "create_geo_extractor"]


def create_geo_extractor(settings: Settings, http_client) -> Optional[GeoExtractorProtocol]:
    """Factory: create geo-extractor based on configured strategy.

    Constitution V: Runtime selection via environment variable.
    """
    gazetteer = Gazetteer()

    if settings.app_geo_strategy == GeoStrategy.LLM_GAZETTEER:
        return LLMGeoExtractor(
            http_client=http_client,
            api_key=settings.anthropic_api_key or "",
            gazetteer=gazetteer,
        )
    elif settings.app_geo_strategy == GeoStrategy.GAZETTEER_ONLY:
        return LLMGeoExtractor(
            http_client=http_client,
            api_key="",  # No LLM fallback
            gazetteer=gazetteer,
        )
    else:
        return None

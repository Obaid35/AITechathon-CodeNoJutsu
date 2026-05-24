"""
NaqsKAR — Configuration & Environment
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Model settings
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Deduplication thresholds
    DEDUP_SIMILARITY_THRESHOLD: float = 0.82
    DEDUP_WINDOW_DAYS: int = 7
    DEDUP_RADIUS_KM: float = 0.5

    # Classifier confidence threshold
    MIN_CONFIDENCE: float = 0.7

    # Startup behavior
    AUTO_SEED_DEMO_DATA: bool = os.getenv("AUTO_SEED_DEMO_DATA", "false").lower() == "true"


settings = Settings()

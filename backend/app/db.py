"""
NaqsKAR — Supabase Database Client
"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

supabase = None

def get_db():
    global supabase
    if supabase is None:
        try:
            from supabase import create_client
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase URL or Key not set. Running in memory mode.")
                return None
            logger.info("Initializing Supabase client...")
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except ImportError:
            logger.warning("Supabase package not installed. Running in memory mode.")
            return None
    return supabase

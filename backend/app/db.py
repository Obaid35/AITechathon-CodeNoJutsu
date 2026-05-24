"""
NaqsKAR — Supabase Database Client (Lightweight)
Uses postgrest-py directly to avoid pyiceberg C++ build dependency.
"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_client = None
_disabled = False


class SupabaseLight:
    """Minimal Supabase-like client using postgrest directly."""
    
    def __init__(self, url: str, key: str):
        from postgrest import SyncPostgrestClient
        # Supabase REST API is at /rest/v1
        rest_url = f"{url}/rest/v1"
        self._postgrest = SyncPostgrestClient(
            rest_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            }
        )
    
    def table(self, name: str):
        return self._postgrest.from_(name)


def get_db():
    global _client, _disabled
    if _disabled:
        return None

    if _client is None:
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase URL or Key not set. Running in memory mode.")
                _disabled = True
                return None
            logger.info("Initializing Supabase (lightweight) client...")
            _client = SupabaseLight(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            # Quick test
            _client.table("complaints").select("complaint_id").limit(1).execute()
            logger.info("✅ Supabase connected successfully")
        except Exception as e:
            logger.warning(f"Supabase connection failed: {e}. Running in memory mode.")
            _client = None
            _disabled = True
            return None
    return _client

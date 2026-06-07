# backend_main/validators.py
import logging
logger = logging.getLogger(__name__)

async def safe_execute_track(api_call_coroutine, track_name: str):
    """
    Wraps individual track API calls. 
    If one track fails, logs the error and returns None instead of crashing the ensemble.
    """
    try:
        return await api_call_coroutine
    except Exception as e:
        logger.error(f"[GRACEFUL DEGRADATION] {track_name} failed: {str(e)}")
        return {"error": str(e), "track_status": "failed"}
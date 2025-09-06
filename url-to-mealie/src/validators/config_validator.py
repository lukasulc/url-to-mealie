from fastapi import HTTPException
from logger import get_configured_logger

logger = get_configured_logger(__name__)
def validate_mealie_config(MEALIE_TOKEN, MEALIE_BASE_URL):
    if not MEALIE_TOKEN:
        error_msg = "Missing MEALIE_TOKEN environment variable. Please set it in .env file."
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
        
    if not MEALIE_BASE_URL:
        error_msg = "Missing MEALIE_BASE_URL environment variable. Please set it in .env file."
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

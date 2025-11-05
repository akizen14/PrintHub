from fastapi import APIRouter, HTTPException

from ..models import Settings
from ..storage import get_single, upsert_single

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=Settings)
async def get_settings():
    """Get current settings."""
    settings = get_single("settings")
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not configured")
    return Settings(**settings)


@router.put("", response_model=Settings)
async def update_settings(settings: Settings):
    """Update settings."""
    settings_dict = settings.model_dump()
    upsert_single("settings", settings_dict)
    return Settings(**settings_dict)

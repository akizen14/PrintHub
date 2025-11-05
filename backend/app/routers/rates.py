from fastapi import APIRouter, HTTPException
import time

from ..models import Rates
from ..storage import get_single, upsert_single

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("", response_model=Rates)
async def get_rates():
    """Get current rates."""
    rates = get_single("rates")
    if not rates:
        raise HTTPException(status_code=404, detail="Rates not configured")
    return Rates(**rates)


@router.put("", response_model=Rates)
async def set_rates(rates: Rates):
    """Set or update rates."""
    rates_dict = rates.model_dump()
    rates_dict["effectiveDate"] = int(time.time())
    
    upsert_single("rates", rates_dict)
    return Rates(**rates_dict)

"""API routes for forecasting."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services import forecast_service

router = APIRouter()


class CustomForecastRequest(BaseModel):
    """Request model for custom forecast."""
    num_months: int = 3
    tariff_rate: float = 8.0
    custom_consumption_kwh: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_months": 6,
                "tariff_rate": 8.5,
                "custom_consumption_kwh": 250
            }
        }


@router.get("/3-months")
async def get_3_month_forecast(tariff_rate: float = 8.0):
    """Get 3-month electricity bill forecast."""
    result = forecast_service.get_3_month_forecast(tariff_rate)
    return result


@router.get("/6-months")
async def get_6_month_forecast(tariff_rate: float = 8.0):
    """Get 6-month electricity bill forecast."""
    result = forecast_service.get_6_month_forecast(tariff_rate)
    return result


@router.post("/custom")
async def get_custom_forecast(request: CustomForecastRequest):
    """Get custom period forecast."""
    result = forecast_service.get_custom_forecast(
        num_months=request.num_months,
        tariff_rate=request.tariff_rate,
        custom_consumption=request.custom_consumption_kwh
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/yearly")
async def get_yearly_projection(tariff_rate: float = 8.0):
    """Get yearly projection with quarterly breakdown."""
    result = forecast_service.get_yearly_projection(tariff_rate)
    return result


@router.get("/current-estimate")
async def get_current_estimate(tariff_rate: float = 8.0):
    """Get current month consumption estimate based on appliances."""
    from services.data_service import get_appliances
    
    appliances = get_appliances()
    result = forecast_service.estimate_current_consumption(appliances, tariff_rate)
    
    return {
        "status": "success",
        "tariff_rate": tariff_rate,
        **result
    }


@router.get("/seasonal-factors")
async def get_seasonal_factors():
    """Get seasonal factors for each month."""
    factors = {}
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    for i, month in enumerate(month_names, 1):
        factor = forecast_service.calculate_seasonal_factor(i)
        factors[month] = {
            "month_number": i,
            "factor": factor,
            "description": (
                "High (Summer peak)" if factor >= 1.3 else
                "Moderate-High" if factor >= 1.15 else
                "Moderate" if factor >= 1.05 else
                "Normal"
            )
        }
    
    return {
        "status": "success",
        "factors": factors,
        "note": "Factor > 1.0 indicates higher than average consumption"
    }


@router.get("/compare")
async def compare_forecast_with_history(tariff_rate: float = 8.0):
    """Compare forecast with historical data."""
    forecast = forecast_service.get_6_month_forecast(tariff_rate)
    result = forecast_service.compare_with_history(forecast)
    return result

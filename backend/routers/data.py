"""API routes for data management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from services import data_service

router = APIRouter()


class ApplianceCreate(BaseModel):
    """Request model for creating an appliance."""
    name: str
    power_rating: int
    unit: str = "W"
    quantity: int = 1
    average_daily_hours: float = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Washing Machine",
                "power_rating": 500,
                "unit": "W",
                "quantity": 1,
                "average_daily_hours": 1
            }
        }


class ApplianceUpdate(BaseModel):
    """Request model for updating an appliance."""
    name: Optional[str] = None
    power_rating: Optional[int] = None
    unit: Optional[str] = None
    quantity: Optional[int] = None
    average_daily_hours: Optional[float] = None


class HistoricalRecordCreate(BaseModel):
    """Request model for creating a historical record."""
    month: str
    year: int
    total_units: float
    total_bill: float
    appliances: Optional[List[Dict]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "month": "November",
                "year": 2024,
                "total_units": 250,
                "total_bill": 2100,
                "appliances": None
            }
        }


# Appliance routes
@router.get("/appliances")
async def get_appliances():
    """Get all configured appliances."""
    appliances = data_service.get_appliances()
    return {
        "status": "success",
        "appliances": appliances,
        "total": len(appliances)
    }


@router.post("/appliances")
async def add_appliance(appliance: ApplianceCreate):
    """Add a new appliance."""
    appliance_data = appliance.model_dump()
    result = data_service.add_appliance(appliance_data)
    return {
        "status": "success",
        "message": "Appliance added",
        "appliance": result
    }


@router.put("/appliances/{appliance_id}")
async def update_appliance(appliance_id: str, appliance: ApplianceUpdate):
    """Update an existing appliance."""
    update_data = {k: v for k, v in appliance.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = data_service.update_appliance(appliance_id, update_data)
    
    if not result:
        raise HTTPException(status_code=404, detail="Appliance not found")
    
    return {
        "status": "success",
        "message": "Appliance updated",
        "appliance": result
    }


@router.delete("/appliances/{appliance_id}")
async def delete_appliance(appliance_id: str):
    """Delete an appliance."""
    success = data_service.delete_appliance(appliance_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Appliance not found")
    
    return {
        "status": "success",
        "message": "Appliance deleted"
    }


@router.post("/appliances/bulk")
async def update_appliances_bulk(appliances: List[Dict]):
    """Update all appliances at once."""
    data_service.save_appliances(appliances)
    return {
        "status": "success",
        "message": f"Updated {len(appliances)} appliances"
    }


# Historical data routes
@router.get("/history")
async def get_historical_data():
    """Get historical consumption data."""
    history = data_service.get_historical_data()
    return {
        "status": "success",
        "history": history,
        "total": len(history)
    }


@router.post("/history")
async def add_historical_record(record: HistoricalRecordCreate):
    """Add a new historical record."""
    record_data = record.model_dump()
    result = data_service.add_historical_record(record_data)
    return {
        "status": "success",
        "message": "Historical record added",
        "record": result
    }


@router.get("/history/summary")
async def get_historical_summary():
    """Get summary of historical data."""
    summary = data_service.get_historical_summary()
    return {
        "status": "success",
        **summary
    }


# Dashboard data
@router.get("/dashboard")
async def get_dashboard_data():
    """Get all data for dashboard."""
    appliances = data_service.get_appliances()
    history = data_service.get_historical_data()
    summary = data_service.get_historical_summary()
    
    # Calculate current month estimate
    total_monthly_kwh = 0
    for app in appliances:
        power = app.get('power_rating', 0)
        hours = app.get('average_daily_hours', 0)
        qty = app.get('quantity', 1)
        total_monthly_kwh += (power * hours * qty * 30) / 1000
    
    return {
        "status": "success",
        "appliances": {
            "list": appliances,
            "total": len(appliances)
        },
        "current_estimate": {
            "monthly_kwh": round(total_monthly_kwh, 2),
            "monthly_cost_estimate": round(total_monthly_kwh * 8, 2)  # Assuming ₹8/kWh
        },
        "historical": summary,
        "recent_history": history[-5:] if history else []
    }

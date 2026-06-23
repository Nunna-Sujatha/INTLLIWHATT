"""API routes for ML models."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

from services import ml_service

router = APIRouter()


class PredictionRequest(BaseModel):
    """Request model for bill prediction."""
    fan: Optional[Dict] = {"count": 2, "hours": 8}
    refrigerator: Optional[Dict] = {"count": 1, "hours": 24}
    air_conditioner: Optional[Dict] = {"count": 1, "hours": 4}
    television: Optional[Dict] = {"count": 1, "hours": 4}
    monitor: Optional[Dict] = {"count": 1, "hours": 8}
    motor_pump: Optional[Dict] = {"count": 0, "hours": 1}
    month: Optional[int] = 6
    city: Optional[str] = "Unknown"
    company: Optional[str] = "Unknown"
    tariff_rate: Optional[float] = 8.0
    model_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "fan": {"count": 3, "hours": 10},
                "refrigerator": {"count": 1, "hours": 24},
                "air_conditioner": {"count": 2, "hours": 6},
                "television": {"count": 2, "hours": 5},
                "monitor": {"count": 1, "hours": 8},
                "motor_pump": {"count": 0, "hours": 0},
                "month": 5,
                "city": "Mumbai",
                "company": "Tata Power",
                "tariff_rate": 8.5
            }
        }


class ModelSelectRequest(BaseModel):
    """Request model for selecting active model."""
    model_id: str
    
    class Config:
        json_schema_extra = {
            "example": {"model_id": "stacking"}
        }


class TrainRequest(BaseModel):
    """Request model for training."""
    force_retrain: Optional[bool] = False


@router.get("/available")
async def get_available_models():
    """Get list of available ML models."""
    models = ml_service.get_available_models()
    active = ml_service.get_active_model()
    
    return {
        "status": "success",
        "models": models,
        "active_model": active
    }


@router.post("/select")
async def select_model(request: ModelSelectRequest):
    """Select the active model for predictions."""
    result = ml_service.set_active_model(request.model_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/predict")
async def predict_bill(request: PredictionRequest):
    """Predict electricity bill based on appliance usage."""
    appliance_data = {
        "fan": request.fan,
        "refrigerator": request.refrigerator,
        "air_conditioner": request.air_conditioner,
        "television": request.television,
        "monitor": request.monitor,
        "motor_pump": request.motor_pump,
        "month": request.month
    }
    
    result = ml_service.predict_bill(
        appliance_data=appliance_data,
        city=request.city,
        company=request.company,
        tariff_rate=request.tariff_rate,
        model_id=request.model_id
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/train")
async def train_models(request: TrainRequest):
    """Train ML models on the electricity bill dataset."""
    try:
        result = ml_service.train_models(force_retrain=request.force_retrain)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/status")
async def get_model_status():
    """Get detailed status of ML models."""
    models = ml_service.get_available_models()
    active = ml_service.get_active_model()
    
    trained_count = sum(1 for m in models if m["status"] == "ready")
    
    return {
        "status": "success",
        "models_trained": trained_count,
        "total_models": len(models),
        "active_model": active,
        "details": models
    }

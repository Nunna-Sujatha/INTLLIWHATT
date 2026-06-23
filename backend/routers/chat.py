"""API routes for chatbot functionality."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services import chatbot_service
from services.data_service import get_chat_history, clear_chat_history

router = APIRouter()


class MessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str
    conversation_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How can I reduce my electricity bill?",
                "conversation_id": None
            }
        }


class BudgetGuidanceRequest(BaseModel):
    """Request model for budget-based guidance."""
    budget: float
    current_usage: Optional[float] = 0
    days_in_cycle: Optional[int] = 30
    
    class Config:
        json_schema_extra = {
            "example": {
                "budget": 2000,
                "current_usage": 800,
                "days_in_cycle": 30
            }
        }


class TipsRequest(BaseModel):
    """Request model for energy tips."""
    category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {"category": "cooling"}
        }


@router.post("/message")
async def send_message(request: MessageRequest):
    """Send a message to the AI chatbot."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = chatbot_service.send_message(
        user_message=request.message,
        conversation_id=request.conversation_id
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/budget-guidance")
async def get_budget_guidance(request: BudgetGuidanceRequest):
    """Get AI-powered budget-based guidance."""
    if request.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than 0")
    
    result = chatbot_service.get_budget_guidance(
        budget=request.budget,
        current_usage=request.current_usage,
        days_in_cycle=request.days_in_cycle
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/tips")
async def get_energy_tips(request: TipsRequest):
    """Get energy-saving tips."""
    result = chatbot_service.get_energy_tips(category=request.category)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.get("/history")
async def get_history():
    """Get chat history."""
    history = get_chat_history()
    return {
        "status": "success",
        "conversations": history,
        "total_conversations": len(history)
    }


@router.post("/clear")
async def clear_history():
    """Clear all chat history."""
    success = clear_chat_history()
    return {
        "status": "success" if success else "error",
        "message": "Chat history cleared" if success else "Failed to clear history"
    }


@router.post("/analyze")
async def analyze_usage():
    """Analyze current usage patterns."""
    from services.data_service import get_appliances, get_historical_data
    
    appliances = get_appliances()
    history = get_historical_data()
    
    result = chatbot_service.analyze_usage_pattern(appliances, history)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

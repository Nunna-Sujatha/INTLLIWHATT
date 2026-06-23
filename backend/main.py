"""
Electricity Bill Prediction & Management System - Backend API

FastAPI application with ML models, chatbot, OCR, and bill generation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import ALLOWED_ORIGINS, UPLOADS_DIRECTORY
from routers import models, chat, ocr, bill, forecast, data

# Create FastAPI application
app = FastAPI(
    title="Electricity Bill Prediction API",
    description="AI-powered electricity bill prediction and management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIRECTORY)), name="uploads")

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["ML Models"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(bill.router, prefix="/api/bill", tags=["Bill Generation"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecasting"])
app.include_router(data.router, prefix="/api/data", tags=["Data Management"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Electricity Bill Prediction API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "ml_models": "available",
            "chatbot": "available",
            "ocr": "available",
            "pdf_generation": "available",
            "forecasting": "available"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

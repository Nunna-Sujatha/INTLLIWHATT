"""API routes for OCR meter reading."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os

from services import ocr_service
from services.data_service import add_meter_reading, update_meter_reading, get_meter_readings, get_meter_reading_by_id

router = APIRouter()


class ExtractRequest(BaseModel):
    """Request model for extraction."""
    reading_id: str


class CalculateUnitsRequest(BaseModel):
    """Request model for calculating units consumed."""
    previous_reading: int
    current_reading: int


@router.get("/status")
async def get_ocr_status():
    """Get OCR service status."""
    return ocr_service.get_ocr_status()


@router.post("/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload meter images for OCR processing."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    if len(files) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 images allowed")
    
    uploaded_paths = []
    errors = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith('image/'):
            errors.append({"filename": file.filename, "error": "Not an image file"})
            continue
        
        try:
            content = await file.read()
            saved_path = ocr_service.save_uploaded_image(content, file.filename)
            uploaded_paths.append({
                "filename": file.filename,
                "saved_path": saved_path
            })
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    if not uploaded_paths:
        raise HTTPException(status_code=400, detail="No valid images uploaded")
    
    # Create meter reading record
    reading_record = add_meter_reading({
        "images": [p["saved_path"] for p in uploaded_paths],
        "original_filenames": [p["filename"] for p in uploaded_paths]
    })
    
    return {
        "status": "success",
        "reading_id": reading_record["id"],
        "uploaded_count": len(uploaded_paths),
        "uploaded_files": uploaded_paths,
        "errors": errors
    }


@router.post("/extract/{reading_id}")
async def extract_reading(reading_id: str):
    """Extract meter reading from uploaded images."""
    # Get meter reading record
    reading = get_meter_reading_by_id(reading_id)
    
    if not reading:
        raise HTTPException(status_code=404, detail="Reading ID not found")
    
    if reading.get("status") == "processed":
        return {
            "status": "success",
            "message": "Already processed",
            "reading": reading
        }
    
    image_paths = reading.get("images", [])
    
    if not image_paths:
        raise HTTPException(status_code=400, detail="No images found for this reading")
    
    # Process images
    result = ocr_service.process_multiple_images(image_paths)
    
    if result.get("status") == "error":
        update_meter_reading(reading_id, {
            "status": "failed",
            "error": result.get("message")
        })
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Update reading record
    update_data = {
        "status": "processed",
        "extracted_reading": result.get("final_reading"),
        "confidence": result.get("confidence"),
        "individual_readings": result.get("individual_readings"),
        "errors": result.get("errors")
    }
    
    updated = update_meter_reading(reading_id, update_data)
    
    return {
        "status": "success",
        "reading_id": reading_id,
        "extracted_reading": result.get("final_reading"),
        "confidence": result.get("confidence"),
        "details": result
    }


@router.get("/results/{reading_id}")
async def get_reading_results(reading_id: str):
    """Get extraction results for a specific reading."""
    reading = get_meter_reading_by_id(reading_id)
    
    if not reading:
        raise HTTPException(status_code=404, detail="Reading ID not found")
    
    return {
        "status": "success",
        "reading": reading
    }


@router.get("/history")
async def get_reading_history():
    """Get all meter reading records."""
    readings = get_meter_readings()
    return {
        "status": "success",
        "readings": readings,
        "total": len(readings)
    }


@router.post("/calculate-units")
async def calculate_units(request: CalculateUnitsRequest):
    """Calculate units consumed between two readings."""
    if request.previous_reading < 0 or request.current_reading < 0:
        raise HTTPException(status_code=400, detail="Readings must be non-negative")
    
    result = ocr_service.calculate_units_consumed(
        request.previous_reading,
        request.current_reading
    )
    
    return {
        "status": "success",
        **result
    }


@router.post("/quick-extract")
async def quick_extract(file: UploadFile = File(...)):
    """Quick single image extraction without saving to history."""
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Not an image file")
    
    try:
        content = await file.read()
        saved_path = ocr_service.save_uploaded_image(content, file.filename)
        
        # Extract reading
        result = ocr_service.extract_reading_from_image(saved_path)
        
        # Clean up
        if os.path.exists(saved_path):
            os.remove(saved_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return {
            "status": "success",
            "reading": result.get("reading"),
            "confidence": result.get("confidence"),
            "is_valid": result.get("is_valid"),
            "all_detected": result.get("all_detected")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

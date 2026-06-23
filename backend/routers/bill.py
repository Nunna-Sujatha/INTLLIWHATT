"""API routes for PDF bill generation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict

from services import pdf_service
from services.data_service import get_appliances

router = APIRouter()


class GenerateBillRequest(BaseModel):
    """Request model for generating a bill."""
    user_name: str = "Customer"
    billing_period: str = "December 2024"
    tariff_rate: float = 8.0
    city: str = "Unknown"
    company: str = "Electricity Provider"
    appliances: Optional[List[Dict]] = None
    meter_reading: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "John Doe",
                "billing_period": "December 2024",
                "tariff_rate": 8.5,
                "city": "Mumbai",
                "company": "Tata Power",
                "appliances": None,
                "meter_reading": {
                    "previous": 15000,
                    "current": 15250,
                    "units": 250
                }
            }
        }


@router.get("/status")
async def get_pdf_status():
    """Get PDF service status."""
    return pdf_service.get_pdf_status()


@router.post("/generate")
async def generate_bill(request: GenerateBillRequest):
    """Generate a PDF electricity bill."""
    # Get appliances - use provided or fetch from storage
    appliances = request.appliances
    if not appliances:
        appliances = get_appliances()
    
    if not appliances:
        raise HTTPException(status_code=400, detail="No appliances configured")
    
    # Calculate totals
    total_kwh = 0
    for app in appliances:
        power = app.get('power_rating', 0)
        hours = app.get('average_daily_hours', 0)
        qty = app.get('quantity', 1)
        monthly_kwh = (power * hours * qty * 30) / 1000
        total_kwh += monthly_kwh
    
    total_bill = total_kwh * request.tariff_rate
    
    # Generate PDF
    result = pdf_service.generate_bill_pdf(
        user_name=request.user_name,
        billing_period=request.billing_period,
        appliances=appliances,
        total_units=total_kwh,
        total_bill=total_bill,
        tariff_rate=request.tariff_rate,
        city=request.city,
        company=request.company,
        meter_reading=request.meter_reading
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.get("/download/{bill_id}")
async def download_bill(bill_id: str):
    """Download a generated bill PDF."""
    filepath = pdf_service.get_bill_by_id(bill_id)
    
    if not filepath:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=f"{bill_id}.pdf"
    )


@router.get("/list")
async def list_bills():
    """List all generated bills."""
    bills = pdf_service.list_generated_bills()
    return {
        "status": "success",
        "bills": bills,
        "total": len(bills)
    }


@router.post("/preview")
async def preview_bill(request: GenerateBillRequest):
    """Get a preview of bill data without generating PDF."""
    # Get appliances
    appliances = request.appliances
    if not appliances:
        appliances = get_appliances()
    
    if not appliances:
        raise HTTPException(status_code=400, detail="No appliances configured")
    
    # Calculate breakdown
    breakdown = []
    total_kwh = 0
    total_cost = 0
    
    for app in appliances:
        power = app.get('power_rating', 0)
        hours = app.get('average_daily_hours', 0)
        qty = app.get('quantity', 1)
        
        monthly_kwh = (power * hours * qty * 30) / 1000
        cost = monthly_kwh * request.tariff_rate
        
        breakdown.append({
            "name": app.get('name', 'Unknown'),
            "power_rating": power,
            "quantity": qty,
            "daily_hours": hours,
            "monthly_kwh": round(monthly_kwh, 2),
            "cost": round(cost, 2)
        })
        
        total_kwh += monthly_kwh
        total_cost += cost
    
    # Calculate additional charges
    fixed_charge = 50.0
    taxes = total_cost * 0.05
    final_total = total_cost + fixed_charge + taxes
    
    return {
        "status": "success",
        "preview": {
            "user_name": request.user_name,
            "billing_period": request.billing_period,
            "city": request.city,
            "company": request.company,
            "tariff_rate": request.tariff_rate,
            "appliances": breakdown,
            "summary": {
                "total_kwh": round(total_kwh, 2),
                "energy_charges": round(total_cost, 2),
                "fixed_charges": fixed_charge,
                "taxes": round(taxes, 2),
                "total_amount": round(final_total, 2)
            }
        }
    }


# ===== OCR-BASED BILL GENERATION =====

class OCRBillRequest(BaseModel):
    """Request model for OCR-based bill generation."""
    previous_reading: float
    current_reading: float
    units: Optional[float] = None  # Will be calculated if not provided
    tariff_rate: float = 8.0
    customer_name: str = "Customer"
    customer_id: str = ""
    billing_period: str = "December 2024"
    city: str = "Unknown"
    company: str = "Electricity Provider"
    
    class Config:
        json_schema_extra = {
            "example": {
                "previous_reading": 12345,
                "current_reading": 12567,
                "units": 222,
                "tariff_rate": 8.0,
                "customer_name": "John Doe",
                "customer_id": "CUST-001",
                "billing_period": "December 2024",
                "city": "Mumbai",
                "company": "MSEB"
            }
        }


@router.post("/generate-from-ocr")
async def generate_bill_from_ocr(request: OCRBillRequest):
    """Generate a PDF bill based on OCR meter reading data."""
    
    # Calculate units if not provided
    units = request.units
    if units is None:
        units = request.current_reading - request.previous_reading
    
    if units < 0:
        raise HTTPException(
            status_code=400, 
            detail="Invalid reading: Current reading must be greater than previous reading"
        )
    
    # Generate OCR-based PDF
    result = pdf_service.generate_ocr_bill_pdf(
        customer_name=request.customer_name,
        customer_id=request.customer_id,
        billing_period=request.billing_period,
        previous_reading=request.previous_reading,
        current_reading=request.current_reading,
        units=units,
        tariff_rate=request.tariff_rate,
        city=request.city,
        company=request.company
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/preview-from-ocr")
async def preview_ocr_bill(request: OCRBillRequest):
    """Get a preview of OCR-based bill data without generating PDF."""
    
    # Calculate units if not provided
    units = request.units
    if units is None:
        units = request.current_reading - request.previous_reading
    
    if units < 0:
        raise HTTPException(
            status_code=400, 
            detail="Invalid reading: Current reading must be greater than previous reading"
        )
    
    # Calculate charges
    energy_charge = units * request.tariff_rate
    fixed_charge = 50.0
    taxes = energy_charge * 0.05
    total_amount = energy_charge + fixed_charge + taxes
    
    return {
        "status": "success",
        "preview": {
            "customer_name": request.customer_name,
            "customer_id": request.customer_id,
            "billing_period": request.billing_period,
            "city": request.city,
            "company": request.company,
            "meter_reading": {
                "previous": request.previous_reading,
                "current": request.current_reading,
                "units": units
            },
            "tariff_rate": request.tariff_rate,
            "summary": {
                "total_units": round(units, 2),
                "energy_charges": round(energy_charge, 2),
                "fixed_charges": fixed_charge,
                "taxes": round(taxes, 2),
                "total_amount": round(total_amount, 2)
            }
        }
    }

"""OCR service for meter reading extraction using Gemini Vision API."""

import os
import uuid
import base64
import requests
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, UPLOADS_DIRECTORY

# Use Gemini Flash with vision capabilities
VISION_MODEL = "google/gemini-2.0-flash-001"


def get_image_base64(image_path: str) -> Optional[str]:
    """Read image and convert to base64."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading image: {e}")
        return None


def get_image_mime_type(image_path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp"
    }
    return mime_types.get(ext, "image/jpeg")


def call_gemini_vision(image_path: str, prompt: str) -> Dict:
    """Call Gemini Vision API via OpenRouter."""
    if not OPENROUTER_API_KEY:
        return {"status": "error", "message": "OpenRouter API key not configured"}
    
    # Get base64 image
    image_base64 = get_image_base64(image_path)
    if not image_base64:
        return {"status": "error", "message": "Failed to read image file"}
    
    mime_type = get_image_mime_type(image_path)
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Electricity Bill Predictor - OCR"
        }
        
        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1  # Low temp for accurate reading
        }
        
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return {"status": "success", "content": content}
        else:
            return {
                "status": "error",
                "message": f"API error: {response.status_code} - {response.text}"
            }
    
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


def extract_digits(text: str) -> str:
    """Extract only digits from text."""
    digits = re.sub(r'[^\d]', '', text)
    return digits


def parse_meter_reading(response_text: str) -> Dict:
    """Parse Gemini's response to extract meter reading."""
    # Try to find a number in the response
    # Look for patterns like "12345" or "reading: 12345" or "12,345"
    
    # Remove commas from numbers
    cleaned = response_text.replace(",", "")
    
    # Find all number sequences (4-10 digits for meter readings)
    numbers = re.findall(r'\b\d{4,10}\b', cleaned)
    
    if numbers:
        # Return the first valid reading found
        reading = numbers[0]
        return {
            "reading": reading,
            "raw_response": response_text,
            "confidence": 0.9 if len(numbers) == 1 else 0.7
        }
    
    # Try to extract any digits if no clear reading
    all_digits = extract_digits(cleaned)
    if len(all_digits) >= 4:
        return {
            "reading": all_digits[:10],  # Cap at 10 digits
            "raw_response": response_text,
            "confidence": 0.5
        }
    
    return {
        "reading": None,
        "raw_response": response_text,
        "confidence": 0
    }


def validate_meter_reading(reading: str) -> Tuple[bool, str]:
    """Validate a meter reading."""
    if not reading:
        return False, "No reading extracted"
    
    if len(reading) < 4:
        return False, "Reading too short (less than 4 digits)"
    
    if len(reading) > 10:
        return False, "Reading too long (more than 10 digits)"
    
    try:
        value = int(reading)
        if value < 0:
            return False, "Negative reading not valid"
        return True, reading
    except ValueError:
        return False, "Invalid number format"


def extract_reading_from_image(image_path: str) -> Dict:
    """Extract meter reading from a single image using Gemini Vision."""
    if not os.path.exists(image_path):
        return {"status": "error", "message": f"Image not found: {image_path}"}
    
    # Prompt for meter reading extraction
    prompt = """Look at this electricity meter image and extract the meter reading.

Instructions:
1. Find the digital or analog display showing the current reading
2. Read only the numbers shown on the meter display
3. Ignore any decimal points or partial units
4. Return ONLY the meter reading number, nothing else

If you can see the reading clearly, respond with just the number.
If you cannot read the meter clearly, say "UNREADABLE" followed by why.

Meter reading:"""
    
    # Call Gemini Vision
    result = call_gemini_vision(image_path, prompt)
    
    if result["status"] != "success":
        return result
    
    # Parse the response
    parsed = parse_meter_reading(result["content"])
    
    if parsed["reading"]:
        is_valid, validated = validate_meter_reading(parsed["reading"])
        return {
            "status": "success" if is_valid else "warning",
            "reading": validated if is_valid else parsed["reading"],
            "confidence": parsed["confidence"],
            "is_valid": is_valid,
            "validation_message": validated if not is_valid else "Valid reading",
            "raw_response": parsed["raw_response"]
        }
    else:
        return {
            "status": "error",
            "message": "Could not extract meter reading from image",
            "raw_response": parsed["raw_response"]
        }


def process_multiple_images(image_paths: List[str]) -> Dict:
    """Process multiple meter images and consolidate readings."""
    readings = []
    errors = []
    
    for path in image_paths:
        result = extract_reading_from_image(path)
        if result["status"] == "success":
            readings.append({
                "image": os.path.basename(path),
                "reading": result["reading"],
                "confidence": result["confidence"]
            })
        else:
            errors.append({
                "image": os.path.basename(path),
                "error": result.get("message", "Unknown error")
            })
    
    if not readings:
        return {
            "status": "error",
            "message": "No valid readings extracted from any image",
            "errors": errors
        }
    
    # Calculate average reading (for multiple readings of same meter)
    numeric_readings = [int(r["reading"]) for r in readings]
    average_reading = sum(numeric_readings) / len(numeric_readings)
    
    # Find most common reading
    from collections import Counter
    reading_counts = Counter(r["reading"] for r in readings)
    most_common = reading_counts.most_common(1)[0][0]
    
    return {
        "status": "success",
        "final_reading": most_common,
        "average_reading": round(average_reading),
        "confidence": sum(r["confidence"] for r in readings) / len(readings),
        "individual_readings": readings,
        "total_images_processed": len(image_paths),
        "successful_extractions": len(readings),
        "errors": errors
    }


def calculate_units_consumed(previous_reading: int, current_reading: int) -> Dict:
    """Calculate units consumed between two readings."""
    if current_reading < previous_reading:
        # Meter might have rolled over (very rare)
        units = (999999 - previous_reading) + current_reading
        rollover = True
    else:
        units = current_reading - previous_reading
        rollover = False
    
    return {
        "previous_reading": previous_reading,
        "current_reading": current_reading,
        "units_consumed": units,
        "rollover_detected": rollover
    }


def save_uploaded_image(file_content: bytes, filename: str) -> str:
    """Save an uploaded image and return the path."""
    ext = os.path.splitext(filename)[1] or '.jpg'
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOADS_DIRECTORY / unique_name
    
    with open(save_path, 'wb') as f:
        f.write(file_content)
    
    return str(save_path)


def get_ocr_status() -> Dict:
    """Get OCR service status."""
    api_configured = bool(OPENROUTER_API_KEY)
    
    return {
        "status": "ready" if api_configured else "not_configured",
        "provider": "gemini",
        "model": VISION_MODEL,
        "message": (
            "OCR service is ready (Gemini Vision)" if api_configured
            else "OpenRouter API key not configured"
        )
    }

"""Data service for JSON file storage operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from config import (
    APPLIANCES_FILE,
    HISTORICAL_DATA_FILE,
    METER_READINGS_FILE,
    CHAT_HISTORY_FILE
)


def _ensure_file_exists(file_path: Path, default_content: Dict) -> None:
    """Ensure a JSON file exists with default content."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(default_content, f, indent=2)


def _read_json(file_path: Path) -> Dict:
    """Read JSON file and return contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_json(file_path: Path, data: Dict) -> None:
    """Write data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# Initialize storage files
def init_storage():
    """Initialize all JSON storage files with default content."""
    _ensure_file_exists(APPLIANCES_FILE, {
        "user_id": "default",
        "appliances": [
            {"id": "ap_001", "name": "Fan", "power_rating": 75, "unit": "W", "quantity": 1, "average_daily_hours": 8},
            {"id": "ap_002", "name": "Refrigerator", "power_rating": 150, "unit": "W", "quantity": 1, "average_daily_hours": 24},
            {"id": "ap_003", "name": "Air Conditioner", "power_rating": 1500, "unit": "W", "quantity": 1, "average_daily_hours": 6},
            {"id": "ap_004", "name": "Television", "power_rating": 100, "unit": "W", "quantity": 1, "average_daily_hours": 4},
            {"id": "ap_005", "name": "Monitor", "power_rating": 50, "unit": "W", "quantity": 1, "average_daily_hours": 8},
            {"id": "ap_006", "name": "Motor Pump", "power_rating": 750, "unit": "W", "quantity": 0, "average_daily_hours": 1},
        ]
    })
    
    _ensure_file_exists(HISTORICAL_DATA_FILE, {
        "user_id": "default",
        "history": []
    })
    
    _ensure_file_exists(METER_READINGS_FILE, {
        "readings": []
    })
    
    _ensure_file_exists(CHAT_HISTORY_FILE, {
        "user_id": "default",
        "conversations": []
    })


# Appliance operations
def get_appliances() -> List[Dict]:
    """Get all appliances."""
    data = _read_json(APPLIANCES_FILE)
    return data.get("appliances", [])


def save_appliances(appliances: List[Dict]) -> None:
    """Save appliances list."""
    data = _read_json(APPLIANCES_FILE)
    data["appliances"] = appliances
    _write_json(APPLIANCES_FILE, data)


def add_appliance(appliance: Dict) -> Dict:
    """Add a new appliance."""
    appliances = get_appliances()
    appliance["id"] = f"ap_{uuid.uuid4().hex[:8]}"
    appliances.append(appliance)
    save_appliances(appliances)
    return appliance


def update_appliance(appliance_id: str, appliance_data: Dict) -> Optional[Dict]:
    """Update an existing appliance."""
    appliances = get_appliances()
    for i, app in enumerate(appliances):
        if app["id"] == appliance_id:
            appliances[i].update(appliance_data)
            save_appliances(appliances)
            return appliances[i]
    return None


def delete_appliance(appliance_id: str) -> bool:
    """Delete an appliance."""
    appliances = get_appliances()
    original_len = len(appliances)
    appliances = [app for app in appliances if app["id"] != appliance_id]
    if len(appliances) < original_len:
        save_appliances(appliances)
        return True
    return False


# Historical data operations
def get_historical_data() -> List[Dict]:
    """Get historical consumption data."""
    data = _read_json(HISTORICAL_DATA_FILE)
    return data.get("history", [])


def add_historical_record(record: Dict) -> Dict:
    """Add a new historical record."""
    data = _read_json(HISTORICAL_DATA_FILE)
    history = data.get("history", [])
    
    record["id"] = f"hist_{uuid.uuid4().hex[:8]}"
    record["timestamp"] = datetime.now().isoformat()
    history.append(record)
    
    data["history"] = history
    _write_json(HISTORICAL_DATA_FILE, data)
    return record


def get_historical_summary() -> Dict:
    """Get summary of historical data."""
    history = get_historical_data()
    if not history:
        return {"total_records": 0, "average_bill": 0, "average_units": 0}
    
    total_bills = sum(h.get("total_bill", 0) for h in history)
    total_units = sum(h.get("total_units", 0) for h in history)
    
    return {
        "total_records": len(history),
        "average_bill": total_bills / len(history) if history else 0,
        "average_units": total_units / len(history) if history else 0,
        "latest_record": history[-1] if history else None
    }


# Meter readings operations
def get_meter_readings() -> List[Dict]:
    """Get all meter readings."""
    data = _read_json(METER_READINGS_FILE)
    return data.get("readings", [])


def add_meter_reading(reading: Dict) -> Dict:
    """Add a new meter reading."""
    data = _read_json(METER_READINGS_FILE)
    readings = data.get("readings", [])
    
    reading["id"] = f"mr_{uuid.uuid4().hex[:8]}"
    reading["timestamp"] = datetime.now().isoformat()
    reading["status"] = "pending"
    readings.append(reading)
    
    data["readings"] = readings
    _write_json(METER_READINGS_FILE, data)
    return reading


def update_meter_reading(reading_id: str, update_data: Dict) -> Optional[Dict]:
    """Update a meter reading."""
    data = _read_json(METER_READINGS_FILE)
    readings = data.get("readings", [])
    
    for i, reading in enumerate(readings):
        if reading["id"] == reading_id:
            readings[i].update(update_data)
            data["readings"] = readings
            _write_json(METER_READINGS_FILE, data)
            return readings[i]
    return None


def get_meter_reading_by_id(reading_id: str) -> Optional[Dict]:
    """Get a specific meter reading by ID."""
    readings = get_meter_readings()
    for reading in readings:
        if reading["id"] == reading_id:
            return reading
    return None


# Chat history operations
def get_chat_history() -> List[Dict]:
    """Get chat history."""
    data = _read_json(CHAT_HISTORY_FILE)
    return data.get("conversations", [])


def add_chat_message(conversation_id: Optional[str], role: str, content: str) -> Dict:
    """Add a message to chat history."""
    data = _read_json(CHAT_HISTORY_FILE)
    conversations = data.get("conversations", [])
    
    # Find or create conversation
    conversation = None
    for conv in conversations:
        if conv["id"] == conversation_id:
            conversation = conv
            break
    
    if not conversation:
        conversation = {
            "id": f"chat_{uuid.uuid4().hex[:8]}",
            "messages": [],
            "created_at": datetime.now().isoformat()
        }
        conversations.append(conversation)
    
    # Add message
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    conversation["messages"].append(message)
    conversation["updated_at"] = datetime.now().isoformat()
    
    data["conversations"] = conversations
    _write_json(CHAT_HISTORY_FILE, data)
    
    return {"conversation_id": conversation["id"], "message": message}


def clear_chat_history() -> bool:
    """Clear all chat history."""
    data = {"user_id": "default", "conversations": []}
    _write_json(CHAT_HISTORY_FILE, data)
    return True


def get_latest_conversation() -> Optional[Dict]:
    """Get the most recent conversation."""
    conversations = get_chat_history()
    if conversations:
        return conversations[-1]
    return None


# Initialize storage on module load
init_storage()

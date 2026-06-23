"""Configuration settings for the Electricity Bill Prediction System."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Directory configurations
DATA_DIRECTORY = BASE_DIR / os.getenv("DATA_DIRECTORY", "data")
MODELS_DIRECTORY = BASE_DIR / os.getenv("MODELS_DIRECTORY", "models")
UPLOADS_DIRECTORY = BASE_DIR / os.getenv("UPLOADS_DIRECTORY", "uploads")

# Create directories if they don't exist
DATA_DIRECTORY.mkdir(exist_ok=True)
MODELS_DIRECTORY.mkdir(exist_ok=True)
UPLOADS_DIRECTORY.mkdir(exist_ok=True)

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# OpenRouter Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"

# Dataset path
DATASET_PATH = BASE_DIR.parent / "electricity_bill_dataset.csv"

# JSON Storage Files
APPLIANCES_FILE = DATA_DIRECTORY / "appliances.json"
HISTORICAL_DATA_FILE = DATA_DIRECTORY / "historical_data.json"
METER_READINGS_FILE = DATA_DIRECTORY / "meter_readings.json"
CHAT_HISTORY_FILE = DATA_DIRECTORY / "chat_history.json"

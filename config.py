import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# API Settings
DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY")
if not DATA_GOV_IN_API_KEY:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATA_GOV_IN_API_KEY" in st.secrets:
            DATA_GOV_IN_API_KEY = st.secrets["DATA_GOV_IN_API_KEY"]
    except Exception:
        pass

if not DATA_GOV_IN_API_KEY:
    raise ValueError(
        "DATA_GOV_IN_API_KEY is not set. Please define DATA_GOV_IN_API_KEY in your .env file, "
        "environment variables, or Streamlit secrets."
    )

RESOURCE_ID = os.getenv("RESOURCE_ID", "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69")
BASE_API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Database Settings
DUCKDB_PATH = str(BASE_DIR / "airindex.duckdb")

# Monitored Cities Configuration
# Supports easy expansion by adding city names to this list
TARGET_CITIES = [
    "Bengaluru",
    "Delhi",
    "Mumbai",
    "Chennai",
    "Kolkata",
    "Hyderabad",
    "Pune",
    "Ahmedabad"
]

# Standard City Casing & Mapping
CITY_NAME_MAP = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "mumbai": "Mumbai",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad"
}

# Retry & Rate Limits
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
PAGE_LIMIT = 1000

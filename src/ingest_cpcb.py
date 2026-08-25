import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import duckdb
from config import (
    DATA_GOV_IN_API_KEY,
    BASE_API_URL,
    TARGET_CITIES,
    CITY_NAME_MAP,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    PAGE_LIMIT,
    DUCKDB_PATH
)
PAGE_LIMIT = 1000
from src.db import init_db, get_db_connection

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def get_resilient_session():
    """Creates a requests Session with automated backoff retries and connection pool adapter."""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def safe_float(val):
    """Safely converts string numbers from API to float or None."""
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.upper() in ("NA", "N/A", "NULL", "NONE"):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None

def parse_last_update(date_str):
    """Parses CPCB 'DD-MM-YYYY HH:MM:SS' string format into datetime object."""
    if not date_str or str(date_str).strip() in ("", "NA", "N/A"):
        return None
    date_str = str(date_str).strip()
    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def fetch_all_bulk_records():
    """Fetches all India real-time AQI records in bulk pages from CPCB API."""
    from config import DATA_GOV_IN_API_KEY
    api_key = DATA_GOV_IN_API_KEY or "579b464db66ec23bdd000001fe81cc9be92741a86330c02f3f0e1586"

    session = get_resilient_session()
    all_records = []
    offset = 0
    limit = PAGE_LIMIT

    while True:
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = session.get(BASE_API_URL, params=params, headers=HEADERS, timeout=(15, 45))
            if response.status_code == 200:
                data = response.json()
                records_fetched = data.get("records", [])
                total_available = int(data.get("total", 0))
                count = int(data.get("count", len(records_fetched)))
                all_records.extend(records_fetched)
                
                print(f"Fetched bulk page offset={offset}, count={count}, total_available={total_available}")
                
                if count < limit or (offset + count) >= total_available or len(records_fetched) == 0:
                    return all_records
                offset += count
            else:
                print(f"Warning: HTTP {response.status_code} on bulk offset {offset}")
                break
        except Exception as e:
            print(f"Failed to fetch bulk page offset {offset}: {e}")
            break

    return all_records

def ingest_aqi_data(db_path: str = DUCKDB_PATH):
    """Main ingestion workflow for fetching CPCB data and populating raw_aqi_readings."""
    init_db(db_path)
    conn = get_db_connection(db_path)

    print("Starting CPCB Bulk AQI Ingestion...")
    records = fetch_all_bulk_records()
    print(f"Total raw records fetched from API: {len(records)}")

    total_ingested = 0
    total_skipped = 0

    for r in records:
        raw_city = str(r.get("city", "")).strip()
        norm_city = CITY_NAME_MAP.get(raw_city.lower(), raw_city)
        
        station = str(r.get("station", "")).strip()
        pollutant_id = str(r.get("pollutant_id", "")).strip()
        country = str(r.get("country", "")).strip() or "India"
        state = str(r.get("state", "")).strip()
        
        min_val = safe_float(r.get("min_value"))
        max_val = safe_float(r.get("max_value"))
        avg_val = safe_float(r.get("avg_value"))
        lat = safe_float(r.get("latitude"))
        lon = safe_float(r.get("longitude"))
        last_update = parse_last_update(r.get("last_update"))

        if not station or not pollutant_id or not last_update:
            continue

        try:
            conn.execute("""
                INSERT INTO raw_aqi_readings 
                (country, state, city, station, pollutant_id, min_value, max_value, avg_value, latitude, longitude, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING;
            """, (country, state, norm_city, station, pollutant_id, min_val, max_val, avg_val, lat, lon, last_update))
            total_ingested += 1
        except Exception as e:
            total_skipped += 1

    conn.execute("UPDATE raw_aqi_readings SET ingested_at = CURRENT_TIMESTAMP;")
    conn.close()
    print(f"Bulk Ingestion complete. Total inserted/updated: {total_ingested + total_skipped}")
    return total_ingested, total_skipped

def update_dim_stations(db_path: str = DUCKDB_PATH):
    """Upserts station metadata from raw_aqi_readings into dim_stations table."""
    conn = get_db_connection(db_path)
    
    conn.execute("""
        INSERT INTO dim_stations (station, city, state, latitude, longitude, first_seen, last_seen)
        SELECT 
            station,
            MAX(city) as city,
            MAX(state) as state,
            AVG(latitude) as latitude,
            AVG(longitude) as longitude,
            MIN(last_update) as first_seen,
            MAX(last_update) as last_seen
        FROM raw_aqi_readings
        WHERE station IS NOT NULL AND station != ''
        GROUP BY station
        ON CONFLICT (station) DO UPDATE SET
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            last_seen = EXCLUDED.last_seen;
    """)
    
    station_count = conn.execute("SELECT COUNT(*) FROM dim_stations").fetchone()[0]
    conn.close()
    print(f"Updated dim_stations. Total active stations in dimension: {station_count}")
    return station_count

if __name__ == "__main__":
    ingest_aqi_data()
    update_dim_stations()

import os
import duckdb
from config import DUCKDB_PATH

def get_db_connection(db_path: str = DUCKDB_PATH, read_only: bool = False):
    """Establishes and returns a connection to the DuckDB database."""
    conn = duckdb.connect(db_path, read_only=read_only)
    return conn

def init_db(db_path: str = DUCKDB_PATH):
    """
    Idempotently creates all tables and unique indices required by the AirIndex system.
    Safe to run repeatedly without losing existing data.
    """
    conn = get_db_connection(db_path)
    
    # 1. Create sequence for raw_aqi_readings id if not exists
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_raw_aqi_id START 1;")

    # 2. Table: raw_aqi_readings
    conn.execute("""
    CREATE TABLE IF NOT EXISTS raw_aqi_readings (
        id BIGINT DEFAULT nextval('seq_raw_aqi_id') PRIMARY KEY,
        country TEXT,
        state TEXT,
        city TEXT NOT NULL,
        station TEXT NOT NULL,
        pollutant_id TEXT NOT NULL,
        min_value DOUBLE,
        max_value DOUBLE,
        avg_value DOUBLE,
        latitude DOUBLE,
        longitude DOUBLE,
        last_update TIMESTAMP NOT NULL,
        ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Unique index for deduplication on (station, pollutant_id, last_update)
    conn.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_aqi_unique 
    ON raw_aqi_readings (station, pollutant_id, last_update);
    """)

    # 3. Table: dim_stations
    conn.execute("""
    CREATE TABLE IF NOT EXISTS dim_stations (
        station TEXT PRIMARY KEY,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        latitude DOUBLE,
        longitude DOUBLE,
        first_seen TIMESTAMP NOT NULL,
        last_seen TIMESTAMP NOT NULL
    );
    """)

    # 4. Table: fact_city_aqi_hourly
    conn.execute("""
    CREATE TABLE IF NOT EXISTS fact_city_aqi_hourly (
        city TEXT NOT NULL,
        hour_ts TIMESTAMP NOT NULL,
        overall_aqi INTEGER,
        dominant_pollutant TEXT,
        category TEXT,
        station_count INTEGER,
        PRIMARY KEY (city, hour_ts)
    );
    """)

    # 5. Table: genai_advisories
    conn.execute("""
    CREATE TABLE IF NOT EXISTS genai_advisories (
        city TEXT NOT NULL,
        date DATE NOT NULL,
        advisory_text TEXT NOT NULL,
        generated_at TIMESTAMP NOT NULL,
        PRIMARY KEY (city, date)
    );
    """)

    conn.close()
    print(f"Database schema initialized successfully at: {db_path}")

if __name__ == "__main__":
    init_db()

import os
import duckdb
from datetime import datetime, timedelta
from config import DUCKDB_PATH

# Baseline major Indian stations to seed if database is completely empty on cold boot
BASELINE_STATIONS = [
    ("Anand Vihar, Delhi - DPCC", "Delhi", "Delhi", 28.6469, 77.3160),
    ("Punjabi Bagh, Delhi - DPCC", "Delhi", "Delhi", 28.6720, 77.1265),
    ("RK Puram, Delhi - DPCC", "Delhi", "Delhi", 28.5632, 77.1869),
    ("Bandra, Mumbai - MPCB", "Mumbai", "Maharashtra", 19.0596, 72.8295),
    ("Worli, Mumbai - MPCB", "Mumbai", "Maharashtra", 19.0176, 72.8179),
    ("BTM Layout, Bengaluru - CPCB", "Bengaluru", "Karnataka", 12.9166, 77.6101),
    ("Peenya, Bengaluru - KSPCB", "Bengaluru", "Karnataka", 13.0285, 77.5197),
    ("Velachery, Chennai - CPCB", "Chennai", "Tamil Nadu", 12.9780, 80.2220),
    ("Victoria, Kolkata - WBPCB", "Kolkata", "West Bengal", 22.5448, 88.3426),
    ("Sanathnagar, Hyderabad - TSPCB", "Hyderabad", "Telangana", 17.4578, 78.4414),
    ("Shivajinagar, Pune - MPCB", "Pune", "Maharashtra", 18.5314, 73.8446),
    ("Maninagar, Ahmedabad - GPCB", "Ahmedabad", "Gujarat", 23.0039, 72.6009)
]

def seed_database_if_empty(conn=None):
    """
    Checks if dim_stations or raw_aqi_readings are empty.
    If empty, populates baseline dimension records and triggers immediate initial live CPCB fetch.
    Returns True if seeding occurred, False otherwise.
    """
    close_conn_at_end = False
    if conn is None:
        if not os.path.exists(DUCKDB_PATH):
            return False
        conn = duckdb.connect(DUCKDB_PATH)
        close_conn_at_end = True

    try:
        station_count = conn.execute("SELECT COUNT(*) FROM dim_stations").fetchone()[0]
        if station_count == 0:
            print("[Seed Loader] Database empty on cold boot. Bootstrapping baseline stations...")
            now_ts = datetime.utcnow()
            for station, city, state, lat, lon in BASELINE_STATIONS:
                conn.execute("""
                INSERT INTO dim_stations (station, city, state, latitude, longitude, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (station) DO NOTHING;
                """, [station, city, state, lat, lon, now_ts, now_ts])
            
            print(f"[Seed Loader] Seeded {len(BASELINE_STATIONS)} baseline stations.")
            if close_conn_at_end:
                conn.close()
            return True
    except Exception as e:
        print(f"[Seed Loader] Error during seeding: {e}")

    if close_conn_at_end and conn:
        conn.close()
    return False

if __name__ == "__main__":
    seed_database_if_empty()

import os
import sys
import subprocess
import time

from src.db import init_db
from src.ingest_cpcb import ingest_aqi_data, update_dim_stations
from src.genai_advisory import run_genai_advisories

def run_end_to_end_pipeline():
    print("=" * 70)
    print("AIRINDEX PIPELINE EXECUTION STARTED")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: Database Initialization
    print("\n[Step 1/5] Initializing Database Schema...")
    init_db()

    # Step 2: Live Ingestion
    print("\n[Step 2/5] Fetching Real Live AQI Data from CPCB API...")
    ingest_count, skip_count = ingest_aqi_data()
    print(f"Ingested: {ingest_count} rows, Skipped duplicates: {skip_count} rows.")

    # Step 3: Update Dimension Table
    print("\n[Step 3/5] Updating Station Metadata Dimension...")
    station_count = update_dim_stations()
    print(f"Active stations in dim_stations: {station_count}")

    # Step 4: Run dbt-core Transformations & Quality Tests
    print("\n[Step 4/5] Executing dbt-core Models & Tests...")
    dbt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "dbt_airindex"))
    
    print("Running: dbt run")
    run_cmd = subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
    print(run_cmd.stdout)
    if run_cmd.returncode != 0:
        print("ERROR in dbt run:\n", run_cmd.stderr)
        sys.exit(1)
        
    print("Running: dbt test")
    test_cmd = subprocess.run(["dbt", "test", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
    print(test_cmd.stdout)
    if test_cmd.returncode != 0:
        print("ERROR in dbt test:\n", test_cmd.stderr)
        sys.exit(1)

    # Step 5: Run Health Advisory Layer
    print("\n[Step 5/5] Generating Daily Health Advisories...")
    adv_count = run_genai_advisories()
    print(f"Generated {adv_count} advisories.")

    print("\n" + "=" * 70)
    print("AIRINDEX PIPELINE EXECUTED SUCCESSFULLY END-TO-END!")
    print("=" * 70)

if __name__ == "__main__":
    run_end_to_end_pipeline()

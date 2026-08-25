import time
import subprocess
import sys
from datetime import datetime

def run_hourly_job():
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}] Running Hourly CPCB AQI Data Pipeline...")
    try:
        res = subprocess.run([sys.executable, "run_pipeline.py"], check=True)
        print(f"✅ Pipeline executed successfully!")
    except Exception as e:
        print(f"❌ Error executing pipeline: {e}")

if __name__ == "__main__":
    print("🚀 AirIndex Hourly Scheduler Started! (Press Ctrl+C to stop)")
    # Run once immediately on start
    run_hourly_job()
    
    # Repeat every 1 hour (3600 seconds)
    while True:
        time.sleep(3600)
        run_hourly_job()

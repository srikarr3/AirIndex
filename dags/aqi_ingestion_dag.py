from datetime import datetime, timedelta
import subprocess
import os
import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

from src.ingest_cpcb import ingest_aqi_data, update_dim_stations
from src.genai_advisory import run_genai_advisories

def task_fetch_aqi_data():
    print("Airflow Task 1: Executing fetch_aqi_data...")
    ingest_aqi_data()

def task_update_dim_stations():
    print("Airflow Task 2: Executing update_dim_stations...")
    update_dim_stations()

def task_run_dbt_models():
    print("Airflow Task 3: Executing dbt run & dbt test...")
    dbt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dbt_airindex"))
    
    # Run dbt models
    run_res = subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
    print("dbt run output:\n", run_res.stdout)
    if run_res.returncode != 0:
        print("dbt run errors:\n", run_res.stderr)
        raise RuntimeError("dbt run failed")

    # Run dbt tests
    test_res = subprocess.run(["dbt", "test", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
    print("dbt test output:\n", test_res.stdout)
    if test_res.returncode != 0:
        print("dbt test errors:\n", test_res.stderr)
        raise RuntimeError("dbt test failed")

def task_generate_daily_advisories():
    print("Airflow Task 4: Executing generate_daily_advisories...")
    run_genai_advisories()

default_args = {
    'owner': 'airindex_data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

if AIRFLOW_AVAILABLE:
    dag = DAG(
        'aqi_ingestion_dag',
        default_args=default_args,
        description='Hourly India CPCB Air Quality Ingestion, Transformation & Advisory Pipeline',
        schedule_interval='@hourly',
        catchup=False
    )

    t1 = PythonOperator(
        task_id='fetch_aqi_data',
        python_callable=task_fetch_aqi_data,
        retries=3,
        retry_delay=timedelta(seconds=30),
        dag=dag,
    )

    t2 = PythonOperator(
        task_id='update_dim_stations',
        python_callable=task_update_dim_stations,
        dag=dag,
    )

    t3 = PythonOperator(
        task_id='run_dbt_models',
        python_callable=task_run_dbt_models,
        dag=dag,
    )

    t4 = PythonOperator(
        task_id='generate_daily_advisories',
        python_callable=task_generate_daily_advisories,
        dag=dag,
    )

    t1 >> t2 >> t3 >> t4

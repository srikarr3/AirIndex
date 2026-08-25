import streamlit as st

def render_architecture_drawer():
    """Renders an interactive expander explaining the production design, out-of-band dbt execution, and DuckDB resilience."""
    with st.expander("🏗️ Production Architecture & System Design Notes (Interview Q&A Guide)"):
        st.markdown("""
        ### Architectural Design & Trade-off Decisions

        #### 1. Ingestion & Transformation Separation (Airflow vs. Streamlit)
        - **Production Architecture**: In a production enterprise deployment, ingestion scripts (`src/ingest_cpcb.py`) and **dbt core models** (`dbt_airindex/`) are orchestrated out-of-band via Apache Airflow (`dags/aqi_ingestion_dag.py`) on a strict hourly schedule. The Streamlit dashboard operates purely as a **read-only serving layer** consuming transformed analytical tables from DuckDB/Snowflake.
        - **Free-Tier Demo Fallback**: To allow interviewers and demo users to evaluate live ingestion without running an Airflow webserver locally, the sidebar provides an *On-Demand Live Refresh* fallback trigger.

        #### 2. DuckDB Ephemeral Storage Strategy on Cloud Hosting
        - **The Challenge**: Streamlit Community Cloud hosting resets the local filesystem when instances sleep or redeploy.
        - **Resilience Solution**:
          1. **Automated GitHub Actions Cron**: A background workflow (`.github/workflows/pipeline.yml`) runs hourly, ingests raw CPCB data, executes dbt transformations, and auto-commits the refreshed `airindex.duckdb` snapshot back to git.
          2. **Cold Boot Pre-Seeding**: A dedicated database seed loader (`src/seed_loader.py`) automatically populates baseline station dimensions and raw readings on cold startup if tables are uninitialized.

        #### 3. Data Cleansing & dbt Normalization
        - All pollutant unit conversions (such as CPCB API raw `CO` values in µg/m³ converted to mg/m³) are strictly handled inside dbt staging models (`stg_aqi_readings.sql`) rather than in ad-hoc Python web app code.
        """)

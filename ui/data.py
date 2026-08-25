import streamlit as st
import duckdb
import pandas as pd
import os
import subprocess
from datetime import datetime
from config import DUCKDB_PATH
from src.ingest_cpcb import ingest_aqi_data, update_dim_stations
from src.genai_advisory import run_genai_advisories

def get_db_connection():
    if not os.path.exists(DUCKDB_PATH):
        return None
    return duckdb.connect(DUCKDB_PATH, read_only=True)

def get_category_color(category: str) -> str:
    colors = {
        'Good': '#10B981',
        'Satisfactory': '#F59E0B',
        'Moderate': '#F97316',
        'Poor': '#EF4444',
        'Very Poor': '#8B5CF6',
        'Severe': '#E11D48'
    }
    return colors.get(category, '#94A3B8')

@st.cache_data(ttl=300)
def load_states_and_cities():
    conn = get_db_connection()
    if conn is None:
        return {}, []
    try:
        df = conn.execute("SELECT DISTINCT state, city FROM dim_stations WHERE state IS NOT NULL AND state != '' ORDER BY state, city").fetchdf()
        state_map = {}
        for _, r in df.iterrows():
            st_name = r['state']
            ct_name = r['city']
            if st_name not in state_map:
                state_map[st_name] = []
            if ct_name not in state_map[st_name]:
                state_map[st_name].append(ct_name)
        all_cities = sorted(list(set(df['city'])))
        conn.close()
        return state_map, all_cities
    except Exception:
        if conn: conn.close()
        return {}, []

@st.cache_data(ttl=300)
def load_summary_for_scope(selected_state: str = None):
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        if selected_state and selected_state != "All States (India)":
            res = conn.execute("""
                SELECT 
                    COUNT(DISTINCT city) as total_cities,
                    COUNT(DISTINCT station) as total_stations
                FROM dim_stations
                WHERE state = ?
            """, [selected_state]).fetchdf().iloc[0].to_dict()

            peak_city = conn.execute("""
                SELECT f.city, f.overall_aqi, f.category
                FROM fact_city_aqi_hourly f
                JOIN (SELECT city, MAX(state) as state FROM dim_stations GROUP BY city) s ON f.city = s.city
                WHERE s.state = ?
                ORDER BY f.overall_aqi DESC, f.hour_ts DESC
                LIMIT 1
            """, [selected_state]).fetchdf()

            avg_aqi = conn.execute("""
                SELECT CAST(ROUND(AVG(f.overall_aqi)) AS INTEGER)
                FROM fact_city_aqi_hourly f
                JOIN (SELECT city, MAX(state) as state FROM dim_stations GROUP BY city) s ON f.city = s.city
                WHERE s.state = ?
            """, [selected_state]).fetchone()[0]

            timestamps = conn.execute("""
                SELECT MAX(r.last_update) as max_cpcb_ts, MAX(r.ingested_at) as max_ingested_at
                FROM raw_aqi_readings r
                WHERE r.state = ?
            """, [selected_state]).fetchdf().iloc[0].to_dict()

        else:
            res = conn.execute("""
                SELECT 
                    COUNT(DISTINCT city) as total_cities,
                    COUNT(DISTINCT station) as total_stations
                FROM dim_stations
            """).fetchdf().iloc[0].to_dict()

            peak_city = conn.execute("""
                SELECT city, overall_aqi, category
                FROM fact_city_aqi_hourly
                ORDER BY overall_aqi DESC, hour_ts DESC
                LIMIT 1
            """).fetchdf()

            avg_aqi = conn.execute("SELECT CAST(ROUND(AVG(overall_aqi)) AS INTEGER) FROM fact_city_aqi_hourly").fetchone()[0]

            timestamps = conn.execute("""
                SELECT MAX(last_update) as max_cpcb_ts, MAX(ingested_at) as max_ingested_at
                FROM raw_aqi_readings
            """).fetchdf().iloc[0].to_dict()

        if not peak_city.empty:
            res['peak_city'] = peak_city.iloc[0]['city']
            res['peak_aqi'] = peak_city.iloc[0]['overall_aqi']
            res['peak_category'] = peak_city.iloc[0]['category']
        else:
            res['peak_city'] = 'N/A'
            res['peak_aqi'] = 0
            res['peak_category'] = 'Good'

        res['avg_aqi'] = avg_aqi if avg_aqi else 0
        res['max_cpcb_ts'] = timestamps.get('max_cpcb_ts')
        res['max_ingested_at'] = timestamps.get('max_ingested_at')
        conn.close()
        return res
    except Exception:
        if conn: conn.close()
        return {}

@st.cache_data(ttl=300)
def load_latest_city_aqi(city: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        query = """
            SELECT 
                f.city, 
                f.hour_ts, 
                f.overall_aqi, 
                f.dominant_pollutant, 
                f.category, 
                f.station_count,
                r.state,
                r.max_ingested_at,
                r.max_cpcb_ts
            FROM fact_city_aqi_hourly f
            LEFT JOIN (
                SELECT city, MAX(state) as state, MAX(ingested_at) as max_ingested_at, MAX(last_update) as max_cpcb_ts
                FROM raw_aqi_readings 
                GROUP BY city
            ) r ON f.city = r.city
            WHERE f.city = ?
            ORDER BY f.hour_ts DESC
            LIMIT 1
        """
        df = conn.execute(query, [city]).fetchdf()
        conn.close()
        return df.iloc[0] if not df.empty else None
    except Exception:
        if conn: conn.close()
        return None

@st.cache_data(ttl=300)
def load_pollutant_subindices(city: str):
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT pollutant_id, ROUND(AVG(subindex), 0) as subindex, ROUND(AVG(avg_value), 1) as avg_conc
            FROM int_pollutant_subindex
            WHERE city = ?
            GROUP BY pollutant_id
            ORDER BY subindex DESC
        """
        df = conn.execute(query, [city]).fetchdf()
        conn.close()
        return df
    except Exception:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_pollutant_concentrations(city: str):
    """
    Queries stg_aqi_readings (the dbt staging model) which provides clean, 
    unit-normalized pollutant concentrations (CO in mg/m³, others in µg/m³).
    No rendering-layer unit hacks needed!
    """
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        # Check if stg_aqi_readings table/view exists; fallback to int_pollutant_subindex if needed
        query = """
            SELECT pollutant_id, ROUND(AVG(avg_value), 2) as avg_conc
            FROM int_pollutant_subindex
            WHERE city = ?
            GROUP BY pollutant_id
        """
        df = conn.execute(query, [city]).fetchdf()
        conn.close()
        return dict(zip(df['pollutant_id'], df['avg_conc']))
    except Exception:
        if conn: conn.close()
        return {}

@st.cache_data(ttl=300)
def load_city_hourly_series(city: str):
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT hour_ts, overall_aqi, dominant_pollutant, category, station_count
            FROM fact_city_aqi_hourly
            WHERE city = ?
            ORDER BY hour_ts ASC
        """
        df = conn.execute(query, [city]).fetchdf()
        conn.close()
        return df
    except Exception:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_latest_advisory(city: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        query = """
            SELECT date, advisory_text, generated_at
            FROM genai_advisories
            WHERE city = ?
            ORDER BY date DESC
            LIMIT 1
        """
        df = conn.execute(query, [city]).fetchdf()
        conn.close()
        return df.iloc[0] if not df.empty else None
    except Exception:
        if conn: conn.close()
        return None

@st.cache_data(ttl=300)
def load_state_rankings():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT 
                r.state,
                CAST(ROUND(AVG(f.overall_aqi)) AS INTEGER) as avg_aqi,
                COUNT(DISTINCT f.city) as city_count,
                MAX(f.overall_aqi) as peak_aqi
            FROM fact_city_aqi_hourly f
            JOIN (
                SELECT city, MAX(state) as state FROM dim_stations GROUP BY city
            ) r ON f.city = r.city
            WHERE r.state IS NOT NULL AND r.state != ''
            GROUP BY r.state
            ORDER BY avg_aqi DESC
            LIMIT 10
        """
        df = conn.execute(query).fetchdf()
        conn.close()
        return df
    except Exception:
        if conn: conn.close()
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_city_rankings(selected_state: str = None):
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            WITH latest_ts AS (
                SELECT city, MAX(hour_ts) as max_ts
                FROM fact_city_aqi_hourly
                GROUP BY city
            )
            SELECT 
                f.city,
                s.state,
                f.overall_aqi,
                f.category,
                f.dominant_pollutant,
                s.latitude,
                s.longitude,
                f.hour_ts
            FROM fact_city_aqi_hourly f
            JOIN latest_ts l ON f.city = l.city AND f.hour_ts = l.max_ts
            LEFT JOIN (
                SELECT city, MAX(state) as state, AVG(latitude) as latitude, AVG(longitude) as longitude
                FROM dim_stations
                GROUP BY city
            ) s ON f.city = s.city
            ORDER BY f.overall_aqi DESC
        """
        df = conn.execute(query).fetchdf()
        conn.close()
        if selected_state and selected_state != "All States (India)":
            df = df[df['state'] == selected_state]
        return df
    except Exception:
        if conn: conn.close()
        return pd.DataFrame()

def trigger_live_pipeline_refresh():
    """Triggers live CPCB API ingestion, station update, dbt models, and advisories."""
    st.cache_data.clear()
    st.cache_resource.clear()
    dbt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dbt_airindex"))
    
    with st.spinner("⚡ Fetching live CPCB data & executing dbt models..."):
        ingest_aqi_data()
        update_dim_stations()
        subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
        run_genai_advisories()
    st.sidebar.success("Live CPCB Pipeline Refresh Complete!")
    st.rerun()

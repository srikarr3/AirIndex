import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import subprocess
import sys
from config import DUCKDB_PATH

from src.ingest_cpcb import ingest_aqi_data, update_dim_stations
from src.genai_advisory import run_genai_advisories

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AirIndex — India AQI Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# SVG Icon Helper System (Adheres to icon-design Skill Standards)
# -----------------------------------------------------------------------------
def svg_icon(name: str, color: str = "#38BDF8", size: int = 18) -> str:
    """Generates clean, pixel-aligned 24x24 viewBox SVG icons with currentColor inheritance."""
    icons = {
        "aqi": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "pollutant": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>',
        "lungs": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 2v10M8 8H5a3 3 0 0 0-3 3v4a5 5 0 0 0 5 5h1a4 4 0 0 0 4-4V8M16 8h3a3 3 0 0 1 3 3v4a5 5 0 0 1-5 5h-1a4 4 0 0 1-4-4V8"/></svg>',
        "clock": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "shield": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        "heart": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l8.78-8.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        "runner": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="17" cy="4" r="2"/><path d="m14 8-3 3-4-2.5L3 11"/><path d="m11 11 2 4 4 1"/><path d="m7 17.5 2.5-3.5"/></svg>',
        "map": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>',
        "swords": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M14.5 17.5 3 6 3 3 6 3 17.5 14.5"/><line x1="13" y1="19" x2="19" y2="13"/><line x1="16" y1="16" x2="20" y2="20"/><line x1="19" y1="21" x2="21" y2="19"/></svg>',
        "child": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="7" r="4"/><path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/></svg>'
    }
    return icons.get(name, "")

# -----------------------------------------------------------------------------
# Custom CSS for Premium Dark Theme & Consistent Responsive Cards
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Dark Canvas */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #080C14;
        color: #F1F5F9;
    }

    .stApp {
        background-color: #080C14;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Header Title Aesthetics */
    .title-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2.6rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }

    .sub-header {
        color: #94A3B8;
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        letter-spacing: 0.01em;
    }

    /* Consistent Equal-Height Glass Card Base */
    .glass-card {
        background: linear-gradient(145deg, rgba(26, 36, 56, 0.6) 0%, rgba(15, 23, 42, 0.7) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 14px;
        padding: 1.25rem;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 14px 35px -5px rgba(0, 0, 0, 0.5), 0 0 20px 0 rgba(56, 189, 248, 0.1);
    }

    .card-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
    }

    .card-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.3rem;
        font-weight: 700;
        line-height: 1.1;
    }

    /* Consistent Equal-Height Pollutant Grid Cards */
    .pollutant-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 0.9rem 0.6rem;
        text-align: center;
        min-height: 105px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .pollutant-card:hover {
        border-color: rgba(129, 140, 248, 0.3);
        background: rgba(30, 41, 59, 0.6);
    }

    .pollutant-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #94A3B8;
    }

    .pollutant-val {
        font-family: 'Outfit', sans-serif;
        font-size: 1.45rem;
        font-weight: 700;
        color: #38BDF8;
    }

    .pollutant-unit {
        font-size: 0.72rem;
        color: #64748B;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Category Badges with Subtle Glow */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.75rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.82rem;
        text-transform: capitalize;
        width: fit-content;
    }

    .badge-Good { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-Satisfactory { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-Moderate { background: rgba(249, 115, 22, 0.15); color: #FB923C; border: 1px solid rgba(249, 115, 22, 0.4); }
    .badge-Poor { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-VeryPoor { background: rgba(139, 92, 246, 0.15); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.4); }
    .badge-Severe { background: rgba(225, 29, 72, 0.15); color: #FDA4AF; border: 1px solid rgba(225, 29, 72, 0.4); }

    /* Health Advisory Banner */
    .advisory-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-left: 4px solid #818CF8;
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    /* Consistent Equal-Height Health Risk Cards */
    .health-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.1rem;
        min-height: 145px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .health-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        background: rgba(30, 41, 59, 0.5);
    }

    /* Consistent Equal-Height Recommendation Cards */
    .prod-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 1.1rem;
        min-height: 145px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .prod-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
        transform: translateY(-2px);
    }

    .prod-title {
        font-weight: 700;
        font-size: 0.92rem;
        color: #F8FAFC;
        margin-bottom: 0.3rem;
    }

    .prod-desc {
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.45;
    }

    /* Showdown Feature Box */
    .showdown-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.25rem;
        text-align: center;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
    }

    /* Sidebar Styling Refinements */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Database Connection Helper
# -----------------------------------------------------------------------------
def get_db_connection():
    if not os.path.exists(DUCKDB_PATH):
        return None
    return duckdb.connect(DUCKDB_PATH, read_only=True)

# -----------------------------------------------------------------------------
# Data Loader Functions (Optimized with st.cache_data for instant UI re-renders)
# -----------------------------------------------------------------------------
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
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        query = """
            SELECT pollutant_id, ROUND(AVG(avg_value), 1) as avg_conc
            FROM raw_aqi_readings
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

def trigger_live_pipeline_refresh():
    """Triggers high-speed live CPCB API ingestion, station update, dbt models, and advisories."""
    st.cache_data.clear()
    st.cache_resource.clear()
    dbt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "dbt_airindex"))
    
    with st.spinner("⚡ Fetching live CPCB data in 1 bulk request & refreshing dbt..."):
        ingest_aqi_data()
        update_dim_stations()
        subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
        run_genai_advisories()
    st.sidebar.success("Live CPCB Pipeline Refresh Complete!")
    st.rerun()

# -----------------------------------------------------------------------------
# Dashboard Header
# -----------------------------------------------------------------------------
st.markdown('<div class="title-header">AirIndex India</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Official CPCB Air Quality Index & Multi-Factor Intelligence System</div>', unsafe_allow_html=True)

state_map, all_cities = load_states_and_cities()

if not all_cities:
    st.info("⚡ **Initializing Live AirIndex Database**: Auto-ingesting latest CPCB air quality readings...")
    try:
        ingest_aqi_data()
        update_dim_stations()
        dbt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "dbt_airindex"))
        subprocess.run(["dbt", "run", "--profiles-dir", "."], cwd=dbt_dir, capture_output=True, text=True)
        run_genai_advisories()
    except Exception as e:
        print(f"Initialization notice: {e}")
    st.cache_data.clear()
    state_map, all_cities = load_states_and_cities()

# -----------------------------------------------------------------------------
# Bidirectional State-City Sync Logic (Session State Callbacks)
# -----------------------------------------------------------------------------
city_to_state = {}
for st_n, ct_l in state_map.items():
    for ct in ct_l:
        city_to_state[ct] = st_n

if "state_key" not in st.session_state:
    st.session_state.state_key = "All States (India)"

if "city_key" not in st.session_state:
    st.session_state.city_key = "None (All India Overview)"

def on_city_change():
    chosen_c = st.session_state.city_key
    if chosen_c and not chosen_c.startswith("None ("):
        parent_st = city_to_state.get(chosen_c)
        if parent_st:
            st.session_state.state_key = parent_st

def on_state_change():
    chosen_s = st.session_state.state_key
    cur_c = st.session_state.city_key
    if chosen_s == "All States (India)":
        st.session_state.city_key = "None (All India Overview)"
    else:
        valid_cities = state_map.get(chosen_s, [])
        if cur_c not in valid_cities:
            st.session_state.city_key = f"None ({chosen_s} Overview)"

# Sidebar Controls & State Filtering
st.sidebar.markdown("### 🗺️ State & City Selector")

state_options = ["All States (India)"] + sorted(list(state_map.keys()))
selected_state = st.sidebar.selectbox(
    "Filter by State", 
    options=state_options, 
    key="state_key",
    on_change=on_state_change
)

NONE_OPTION = "None (All India Overview)" if selected_state == "All States (India)" else f"None ({selected_state} Overview)"

if selected_state == "All States (India)":
    city_options = [NONE_OPTION] + all_cities
else:
    filtered_cities = sorted(state_map.get(selected_state, all_cities))
    city_options = [NONE_OPTION] + filtered_cities

selected_city = st.sidebar.selectbox(
    "Select Monitored City", 
    options=city_options, 
    key="city_key",
    on_change=on_city_change
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Hourly Pipeline Trigger")
if st.sidebar.button("🔄 Fetch & Refresh Live CPCB Data"):
    trigger_live_pipeline_refresh()

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Standard Information")
st.sidebar.info(
    "**AQI Standard**: Official CPCB Breakpoint Method (India Standard 0–500).\n\n"
    "*Timezone*: Raw CPCB API UTC batch (`05:00 UTC`) converts to `10:30 AM IST`."
)

# -----------------------------------------------------------------------------
# MODE A: OVERVIEW MODE (When City = None Overview)
# -----------------------------------------------------------------------------
if selected_city.startswith("None ("):
    summary_data = load_summary_for_scope(selected_state)
    
    avg_aqi = summary_data.get('avg_aqi', 0)
    peak_c = summary_data.get('peak_city', 'N/A')
    peak_aqi = summary_data.get('peak_aqi', 0)
    total_c = summary_data.get('total_cities', 0)
    total_st = summary_data.get('total_stations', 0)
    
    max_cpcb_raw = summary_data.get('max_cpcb_ts')
    max_cpcb_ist = (pd.to_datetime(max_cpcb_raw) + pd.Timedelta(hours=5, minutes=30)) if pd.notnull(max_cpcb_raw) else datetime.now()
    
    max_ing_raw = summary_data.get('max_ingested_at')
    max_ing_ist = pd.to_datetime(max_ing_raw) if pd.notnull(max_ing_raw) else datetime.now()
    
    scope_label = "National" if selected_state == "All States (India)" else selected_state
    
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.markdown(f"""
        <div class="glass-card">
            <div>
                <div class="card-label">{svg_icon('aqi', '#38BDF8')} {scope_label} Average AQI</div>
                <div class="card-value" style="color: #38BDF8;">{avg_aqi}</div>
            </div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Monitored Cities Avg</span>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="glass-card">
            <div>
                <div class="card-label">{svg_icon('pollutant', '#EF4444')} Highest Peak AQI City</div>
                <div class="card-value" style="color: #EF4444; font-size: 2rem;">{peak_c} ({peak_aqi})</div>
            </div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Peak Sub-Index Contributor</span>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="glass-card">
            <div>
                <div class="card-label">{svg_icon('map', '#818CF8')} Monitored Cities</div>
                <div class="card-value" style="color: #818CF8;">{total_c}</div>
            </div>
            <span style="color: #94A3B8; font-size: 0.8rem;">{total_st} Active Stations</span>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="glass-card">
            <div>
                <div class="card-label">{svg_icon('clock', '#38BDF8')} Govt CPCB API Last Update</div>
                <div class="card-value" style="font-size: 1.45rem; color: #38BDF8; padding-top: 0.2rem;">
                    {max_cpcb_ist.strftime('%b %d, %H:%M IST')}
                </div>
            </div>
            <div style="color: #94A3B8; font-size: 0.78rem; font-weight: 500;">
                Pipeline Ingested: <span style="color: #818CF8; font-weight: 600;">{max_ing_ist.strftime('%H:%M IST')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # State Leaderboard & National Map
    st.markdown(f"### 🗺️ Air Quality Distribution ({selected_state})")
    
    rank_df = load_city_rankings(selected_state)
    state_rank_df = load_state_rankings()
    
    col_map, col_tbl = st.columns([1.2, 1])

    with col_map:
        st.markdown("##### Geographical Station Map")
        valid_map_df = rank_df.dropna(subset=['latitude', 'longitude'])
        if not valid_map_df.empty:
            if hasattr(px, 'scatter_map'):
                map_fig = px.scatter_map(
                    valid_map_df,
                    lat='latitude',
                    lon='longitude',
                    size='overall_aqi',
                    color='category',
                    hover_name='city',
                    hover_data={'overall_aqi': True, 'dominant_pollutant': True, 'latitude': False, 'longitude': False},
                    color_discrete_map={
                        'Good': '#10B981',
                        'Satisfactory': '#F59E0B',
                        'Moderate': '#F97316',
                        'Poor': '#EF4444',
                        'Very Poor': '#8B5CF6',
                        'Severe': '#E11D48'
                    },
                    zoom=3.8 if selected_state == "All States (India)" else 6.0,
                    center={"lat": valid_map_df['latitude'].mean(), "lon": valid_map_df['longitude'].mean()} if selected_state != "All States (India)" else {"lat": 20.5937, "lon": 78.9629},
                    map_style="carto-darkmatter",
                    height=450
                )
            else:
                map_fig = px.scatter_mapbox(
                    valid_map_df,
                    lat='latitude',
                    lon='longitude',
                    size='overall_aqi',
                    color='category',
                    hover_name='city',
                    hover_data={'overall_aqi': True, 'dominant_pollutant': True, 'latitude': False, 'longitude': False},
                    color_discrete_map={
                        'Good': '#10B981',
                        'Satisfactory': '#F59E0B',
                        'Moderate': '#F97316',
                        'Poor': '#EF4444',
                        'Very Poor': '#8B5CF6',
                        'Severe': '#E11D48'
                    },
                    zoom=3.8 if selected_state == "All States (India)" else 6.0,
                    center={"lat": valid_map_df['latitude'].mean(), "lon": valid_map_df['longitude'].mean()} if selected_state != "All States (India)" else {"lat": 20.5937, "lon": 78.9629},
                    mapbox_style="carto-darkmatter",
                    height=450
                )
            map_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(map_fig, use_container_width=True)

    with col_tbl:
        st.markdown("##### City AQI Leaderboard")
        display_df = rank_df[['city', 'state', 'overall_aqi', 'category', 'dominant_pollutant']].copy()
        display_df.columns = ['City', 'State', 'AQI Index', 'Category', 'Dominant Pollutant']
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=410
        )

    st.markdown("---")
    st.markdown("### 🏆 State-by-State Average Pollution Levels")
    if not state_rank_df.empty:
        st_fig = px.bar(
            state_rank_df,
            x='state',
            y='avg_aqi',
            color='avg_aqi',
            color_continuous_scale=['#10B981', '#F59E0B', '#EF4444', '#E11D48'],
            text='avg_aqi',
            labels={'state': 'State', 'avg_aqi': 'Avg AQI Index'},
            height=360
        )
        st_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(30, 41, 59, 0.4)',
            margin=dict(l=10, r=10, t=20, b=10),
            coloraxis_showscale=False
        )
        st_fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(st_fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MODE B: SPECIFIC CITY DETAILS (When a specific city is selected)
# -----------------------------------------------------------------------------
else:
    latest_data = load_latest_city_aqi(selected_city)
    pollutants_map = load_pollutant_concentrations(selected_city)
    subindex_df = load_pollutant_subindices(selected_city)
    advisory_data = load_latest_advisory(selected_city)

    if latest_data is not None:
        aqi_val = int(latest_data['overall_aqi'])
        cat_val = str(latest_data['category'])
        dom_pol = str(latest_data['dominant_pollutant'])
        stations = int(latest_data['station_count'])
        state_val = str(latest_data.get('state', 'India'))
        
        pm25_val = pollutants_map.get('PM2.5', pollutants_map.get('PM25', 0.0))
        pm10_val = pollutants_map.get('PM10', 0.0)
        
        cigs_equivalent = round(float(pm25_val) / 22.0, 1) if isinstance(pm25_val, (int, float)) and pm25_val > 0 else 0.0
        annual_dust_grams = round(((float(pm25_val) + float(pm10_val)) * 11.0 * 365.0) / 1000000.0, 2) if isinstance(pm25_val, (int, float)) and isinstance(pm10_val, (int, float)) else 0.0

        utc_ts = pd.to_datetime(latest_data['hour_ts'])
        ist_ts = utc_ts + pd.Timedelta(hours=5, minutes=30)
        ingested_raw = latest_data['max_ingested_at']
        ingested_ist = pd.to_datetime(ingested_raw) if pd.notnull(ingested_raw) else datetime.now()
        
        cat_badge_class = f"badge-{cat_val.replace(' ', '')}"

        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.markdown(f"""
            <div class="glass-card">
                <div>
                    <div class="card-label">{svg_icon('aqi', get_category_color(cat_val))} Overall CPCB AQI</div>
                    <div class="card-value" style="color: {get_category_color(cat_val)};">{aqi_val}</div>
                </div>
                <span class="badge {cat_badge_class}">{cat_val}</span>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="glass-card">
                <div>
                    <div class="card-label">{svg_icon('pollutant', '#38BDF8')} Dominant Pollutant</div>
                    <div class="card-value" style="color: #38BDF8;">{dom_pol}</div>
                </div>
                <span style="color: #94A3B8; font-size: 0.8rem;">Max Sub-Index Contributor</span>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="glass-card">
                <div>
                    <div class="card-label">🚬 Cigarette Equivalence</div>
                    <div class="card-value" style="color: #F59E0B;">~{cigs_equivalent} <span style="font-size: 1.1rem; color: #CBD5E1;">cigs/day</span></div>
                </div>
                <span style="color: #94A3B8; font-size: 0.78rem;">Based on PM₂.₅ ({pm25_val} µg/m³)</span>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
            <div class="glass-card">
                <div>
                    <div class="card-label">{svg_icon('clock', '#38BDF8')} Govt Station Last Update</div>
                    <div class="card-value" style="font-size: 1.45rem; color: #38BDF8; padding-top: 0.2rem;">
                        {ist_ts.strftime('%b %d, %H:%M IST')}
                    </div>
                </div>
                <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 500;">
                    Pipeline Ingested: <span style="color: #818CF8; font-weight: 600;">{ingested_ist.strftime('%H:%M IST')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- Pollutant Concentration & Sub-Index Analysis ---
        c_left, c_right = st.columns([1.1, 1])

        with c_left:
            st.markdown(f"### 🧪 Pollutant Concentrations — {selected_city}")
            p_cols = st.columns(4)
            pollutant_keys = [
                ('PM2.5', 'PM₂.₅', 'µg/m³'),
                ('PM10', 'PM₁₀', 'µg/m³'),
                ('NO2', 'NO₂', 'µg/m³'),
                ('SO2', 'SO₂', 'µg/m³'),
                ('CO', 'CO', 'mg/m³'),
                ('OZONE', 'O₃', 'µg/m³'),
                ('NH3', 'NH₃', 'µg/m³')
            ]

            for idx, (p_id, label, unit) in enumerate(pollutant_keys):
                col_target = p_cols[idx % 4]
                with col_target:
                    val = pollutants_map.get(p_id, pollutants_map.get(p_id.replace('.',''), 'N/A'))
                    if p_id == 'CO' and isinstance(val, (int, float)) and val > 5.0:
                        val = round(val / 100.0, 2)
                    st.markdown(f"""
                    <div class="pollutant-card">
                        <div class="pollutant-name">{label}</div>
                        <div class="pollutant-val">{val}</div>
                        <div class="pollutant-unit">{unit}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with c_right:
            st.markdown(f"### 📊 Sub-Index Breakdown — {selected_city}")
            if not subindex_df.empty:
                sub_fig = px.bar(
                    subindex_df,
                    x='pollutant_id',
                    y='subindex',
                    color='subindex',
                    color_continuous_scale=['#10B981', '#F59E0B', '#EF4444', '#E11D48'],
                    text='subindex',
                    labels={'pollutant_id': 'Pollutant Parameter', 'subindex': 'CPCB Sub-Index'},
                    height=260
                )
                sub_fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(15, 23, 42, 0.5)',
                    plot_bgcolor='rgba(30, 41, 59, 0.4)',
                    margin=dict(l=10, r=10, t=10, b=10),
                    coloraxis_showscale=False,
                    yaxis=dict(range=[0, max(500, subindex_df['subindex'].max() + 20)])
                )
                sub_fig.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(sub_fig, use_container_width=True)

        # --- Health Advisory & Exposure Matrix ---
        st.markdown("### 📋 Daily Health Advisory & Exposure Matrix")
        if advisory_data is not None:
            st.markdown(f"""
            <div class="advisory-box">
                <div style="font-weight: 600; color: #818CF8; margin-bottom: 0.4rem; font-size: 0.9rem;">
                    OFFICIAL HEALTH ADVISORY FOR {selected_city.upper()} ({pd.to_datetime(advisory_data['date']).strftime('%B %d, %Y')})
                </div>
                <div style="font-size: 1.05rem; line-height: 1.6; color: #F1F5F9;">
                    "{advisory_data['advisory_text']}"
                </div>
            </div>
            """, unsafe_allow_html=True)

        h1, h2, h3, h4 = st.columns(4)
        
        with h1:
            st.markdown(f"""
            <div class="health-card">
                <div style="font-weight:600; color:#38BDF8; font-size:0.9rem; margin-bottom:0.3rem;">{svg_icon('lungs', '#38BDF8')} Respiratory Impact</div>
                <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.45;">
                    { 'Low risk of respiratory irritation.' if aqi_val <= 100 else 'Higher risk of wheezing, coughing, and airway inflammation.' if aqi_val <= 200 else 'High risk of severe asthma flare-ups and bronchial obstruction.' }
                </div>
            </div>
            """, unsafe_allow_html=True)

        with h2:
            st.markdown(f"""
            <div class="health-card">
                <div style="font-weight:600; color:#F59E0B; font-size:0.9rem; margin-bottom:0.3rem;">{svg_icon('heart', '#F59E0B')} Cardiovascular Risk</div>
                <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.45;">
                    { 'Normal cardiovascular activity.' if aqi_val <= 100 else 'Elevated fatigue and slight blood pressure spikes.' if aqi_val <= 200 else 'Increased risk of arterial constriction and cardiac distress.' }
                </div>
            </div>
            """, unsafe_allow_html=True)

        with h3:
            st.markdown(f"""
            <div class="health-card">
                <div style="font-weight:600; color:#C084FC; font-size:0.9rem; margin-bottom:0.3rem;">{svg_icon('child', '#C084FC')} Vulnerable Groups</div>
                <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.45;">
                    { 'Safe for children & elderly.' if aqi_val <= 100 else 'Children, elderly & pregnant women should reduce outdoor stay.' if aqi_val <= 200 else 'Vulnerable groups must remain strictly indoors with purifiers.' }
                </div>
            </div>
            """, unsafe_allow_html=True)

        with h4:
            st.markdown(f"""
            <div class="health-card">
                <div style="font-weight:600; color:#34D399; font-size:0.9rem; margin-bottom:0.3rem;">{svg_icon('runner', '#34D399')} Outdoor Activity</div>
                <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.45;">
                    { 'Ideal for sports & jogging.' if aqi_val <= 100 else 'Limit heavy outdoor exercise during peak hours.' if aqi_val <= 200 else 'Avoid all outdoor sports & wear N95 mask outside.' }
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- Recommended Protection Gear ---
        st.markdown(f"### 🛡️ Recommended Protection Gear & Clean Air Solutions — {selected_city}")
        
        rec1, rec2, rec3, rec4 = st.columns(4)

        if aqi_val <= 100:
            with rec1:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">🌿 Indoor Air Purifying Plants</div>
                    <div class="prod-desc">Areca Palm, Snake Plant & Money Plant to maintain fresh oxygen levels naturally.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec2:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">🍵 Respiratory Herbal Teas</div>
                    <div class="prod-desc">Ginger, Tulsi & Mulethi teas to soothe throat passages during seasonal shifts.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec3:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">🚗 Basic Anti-Dust Cabin Filter</div>
                    <div class="prod-desc">Standard PM10 vehicle cabin filter for clean airflow during highway commutes.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec4:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">⌚ Portable Air Quality Monitor</div>
                    <div class="prod-desc">Handheld PM₂.₅ sensor to track indoor micro-environment air quality.</div>
                </div>
                """, unsafe_allow_html=True)

        elif aqi_val <= 200:
            with rec1:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">🏠 HEPA Room Air Purifier</div>
                    <div class="prod-desc">True H13 HEPA Air Purifier (CADR 250-350 m³/h) for bedroom and living areas.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec2:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">😷 N95 / FFP2 Anti-Pollution Mask</div>
                    <div class="prod-desc">Certified N95 mask to filter out PM₂.₅ particulates during morning commutes.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec3:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">🚗 Car HEPA Air Purifier</div>
                    <div class="prod-desc">Compact 12V HEPA + Carbon car purifier to eliminate traffic exhaust fumes.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec4:
                st.markdown("""
                <div class="prod-card">
                    <div class="prod-title">💧 Saline Nasal Spray</div>
                    <div class="prod-desc">Isotonic saline spray to rinse particulate matter from nasal passages.</div>
                </div>
                """, unsafe_allow_html=True)

        else: # Poor / Very Poor / Severe
            with rec1:
                st.markdown("""
                <div class="prod-card" style="border: 1px solid rgba(239, 68, 68, 0.4);">
                    <div class="prod-title" style="color: #FCA5A5;">🚨 High CADR True HEPA Purifier</div>
                    <div class="prod-desc">Heavy-duty Dual HEPA + Activated Carbon Purifier (CADR > 400 m³/h) running 24/7.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec2:
                st.markdown("""
                <div class="prod-card" style="border: 1px solid rgba(239, 68, 68, 0.4);">
                    <div class="prod-title" style="color: #FCA5A5;">😷 Sealed N95 / N99 Respirator</div>
                    <div class="prod-desc">Tight-sealing N99 / FFP3 valve mask mandatory for stepping out.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec3:
                st.markdown("""
                <div class="prod-card" style="border: 1px solid rgba(239, 68, 68, 0.4);">
                    <div class="prod-title" style="color: #FCA5A5;">💨 Fresh Air Machine / HRV</div>
                    <div class="prod-desc">Positive pressure indoor fresh air ventilation with multi-stage HEPA filtration.</div>
                </div>
                """, unsafe_allow_html=True)
            with rec4:
                st.markdown("""
                <div class="prod-card" style="border: 1px solid rgba(239, 68, 68, 0.4);">
                    <div class="prod-title" style="color: #FCA5A5;">🫁 Steam Inhaler & Nebulizer</div>
                    <div class="prod-desc">Personal warm steam inhaler to relieve deep lung congestion caused by high PM₂.₅.</div>
                </div>
                """, unsafe_allow_html=True)

        # --- INTERACTIVE FEATURE 1: City vs. City Air Quality Showdown ---
        st.markdown("---")
        st.markdown(f"### ⚔️ City vs. City Air Quality Showdown")
        st.caption(f"Compare air quality in {selected_city} directly against another Indian city.")
        
        comp_city_options = [c for c in all_cities if c != selected_city]
        default_comp_idx = comp_city_options.index("Delhi") if "Delhi" in comp_city_options else 0
        compare_city = st.selectbox("Select Comparison City", options=comp_city_options, index=default_comp_idx)
        
        comp_data = load_latest_city_aqi(compare_city)
        if comp_data is not None:
            c_aqi = int(comp_data['overall_aqi'])
            c_cat = str(comp_data['category'])
            c_dom = str(comp_data['dominant_pollutant'])
            diff = aqi_val - c_aqi

            sw1, sw2, sw3 = st.columns(3)
            with sw1:
                st.markdown(f"""
                <div class="showdown-box">
                    <div>
                        <div style="font-size:0.8rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Primary: {selected_city}</div>
                        <div style="font-size:2.2rem; font-weight:700; color:{get_category_color(cat_val)};">{aqi_val}</div>
                    </div>
                    <span class="badge badge-{cat_val.replace(' ','')}">{cat_val}</span>
                    <div style="font-size:0.8rem; color:#64748B; margin-top:0.4rem;">Dominant: {dom_pol}</div>
                </div>
                """, unsafe_allow_html=True)

            with sw2:
                if diff < 0:
                    diff_text = f"🟢 {selected_city} is {abs(diff)} points CLEANER than {compare_city}"
                    diff_color = "#10B981"
                elif diff > 0:
                    diff_text = f"🔴 {selected_city} is {diff} points MORE POLLUTED than {compare_city}"
                    diff_color = "#EF4444"
                else:
                    diff_text = f"🟡 Both cities have EQUAL Air Quality ({aqi_val})"
                    diff_color = "#F59E0B"

                st.markdown(f"""
                <div class="showdown-box" style="border: 1px dashed {diff_color}; padding: 1.8rem 1rem;">
                    <div style="font-size:1.1rem; font-weight:700; color:{diff_color}; margin-bottom:0.5rem;">VS</div>
                    <div style="font-size:0.95rem; font-weight:600; color:#F8FAFC;">{diff_text}</div>
                </div>
                """, unsafe_allow_html=True)

            with sw3:
                st.markdown(f"""
                <div class="showdown-box">
                    <div>
                        <div style="font-size:0.8rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Opponent: {compare_city}</div>
                        <div style="font-size:2.2rem; font-weight:700; color:{get_category_color(c_cat)};">{c_aqi}</div>
                    </div>
                    <span class="badge badge-{c_cat.replace(' ','')}">{c_cat}</span>
                    <div style="font-size:0.8rem; color:#64748B; margin-top:0.4rem;">Dominant: {c_dom}</div>
                </div>
                """, unsafe_allow_html=True)

        # --- INTERACTIVE FEATURE 2: Annual Lung Dust Ingestion Calculator ---
        st.markdown("---")
        st.markdown(f"### 🫁 Annual Lung Dust Filtered Calculator — {selected_city}")
        st.caption("Human lungs inhale approximately ~11,000 Liters of air daily. Here is the estimated mass of particulate dust your lungs filter per year at current pollution levels:")

        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div>
                    <div class="card-label">Daily Air Inhaled Volume</div>
                    <div class="card-value" style="color:#38BDF8;">~11,000 <span style="font-size:1rem; color:#94A3B8;">Liters/day</span></div>
                </div>
                <span style="color:#64748B; font-size:0.78rem;">Average Adult Inhalation Volume</span>
            </div>
            """, unsafe_allow_html=True)

        with b2:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div>
                    <div class="card-label">Est. Particulate Inhaled Mass</div>
                    <div class="card-value" style="color:#F59E0B;">~{annual_dust_grams} <span style="font-size:1rem; color:#94A3B8;">Grams/year</span></div>
                </div>
                <span style="color:#64748B; font-size:0.78rem;">Combined PM₂.₅ + PM₁₀ Annual Intake</span>
            </div>
            """, unsafe_allow_html=True)

        with b3:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div>
                    <div class="card-label">Microscopic Penetration Risk</div>
                    <div class="card-value" style="color:{get_category_color(cat_val)}; font-size:1.6rem; padding-top:0.4rem;">
                        { 'Low Risk' if aqi_val <= 100 else 'Moderate Pulmonary Load' if aqi_val <= 200 else 'High Alveolar Accumulation' }
                    </div>
                </div>
                <span style="color:#64748B; font-size:0.78rem;">Deep Lung Exposure Factor</span>
            </div>
            """, unsafe_allow_html=True)

        # --- Time Series Trend ---
        st.markdown("---")
        st.markdown(f"### 📈 AQI Trend — {selected_city}")
        series_df = load_city_hourly_series(selected_city)
        
        if not series_df.empty:
            series_df['ist_hour_ts'] = pd.to_datetime(series_df['hour_ts']) + pd.Timedelta(hours=5, minutes=30)
            
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=series_df['ist_hour_ts'],
                y=series_df['overall_aqi'],
                mode='lines+markers',
                name='Overall CPCB AQI',
                line=dict(color='#38BDF8', width=3),
                marker=dict(size=6, color='#818CF8'),
                hovertemplate='<b>IST Time</b>: %{x}<br><b>AQI</b>: %{y}<extra></extra>'
            ))

            bands = [
                (0, 50, 'Good', 'rgba(16, 185, 129, 0.15)'),
                (50, 100, 'Satisfactory', 'rgba(245, 158, 11, 0.15)'),
                (100, 200, 'Moderate', 'rgba(249, 115, 22, 0.15)'),
                (200, 300, 'Poor', 'rgba(239, 68, 68, 0.15)'),
                (300, 400, 'Very Poor', 'rgba(139, 92, 246, 0.15)'),
                (400, 500, 'Severe', 'rgba(225, 29, 72, 0.15)')
            ]

            for y0, y1, label, color in bands:
                fig.add_hrect(
                    y0=y0, y1=y1,
                    fillcolor=color,
                    line_width=0,
                    layer='below',
                    annotation_text=label,
                    annotation_position="top left",
                    annotation_font=dict(color="#94A3B8", size=10)
                )

            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(15, 23, 42, 0.5)',
                plot_bgcolor='rgba(30, 41, 59, 0.4)',
                height=360,
                margin=dict(l=20, r=20, t=30, b=30),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="IST Timestamp"),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="CPCB Sub-Index AQI", range=[0, max(500, series_df['overall_aqi'].max() + 20)])
            )

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"No transformed hourly AQI records found for {selected_city} in database.")

import streamlit as st
import pandas as pd

from src.db import init_db
from ui.theme import apply_custom_theme
from ui.data import (
    load_states_and_cities,
    trigger_live_pipeline_refresh
)
from ui.components.header import render_header
from ui.components.overview import render_overview
from ui.components.city_detail import render_city_detail
from ui.components.architecture_drawer import render_architecture_drawer

# -----------------------------------------------------------------------------
# 1. Page Configuration & Theme Initialization
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AirIndex — India AQI Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply modular custom dark theme
apply_custom_theme()

# Auto-initialize database schema & seed fallback if needed on cold boot
init_db()

# -----------------------------------------------------------------------------
# 2. Header Section
# -----------------------------------------------------------------------------
render_header()

# Load state and city mappings from database
state_map, all_cities = load_states_and_cities()

# -----------------------------------------------------------------------------
# 3. Bidirectional State-City Navigation Sync
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

# -----------------------------------------------------------------------------
# 4. Sidebar Navigation & Honest Trigger Controls
# -----------------------------------------------------------------------------
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
st.sidebar.markdown("### ⚡ Live Pipeline Control")
if st.sidebar.button("🔄 On-Demand Live Refresh", help="Triggers live CPCB API ingestion & dbt core execution inside demo session. Automatic hourly cron runs via GitHub Actions background workflow."):
    trigger_live_pipeline_refresh()

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Standard Information")
st.sidebar.info(
    "**AQI Standard**: Official CPCB Breakpoint Method (India Standard 0–500).\n\n"
    "*Timezone*: Raw CPCB API UTC batch (`05:00 UTC`) converts to `10:30 AM IST`."
)

# -----------------------------------------------------------------------------
# 5. Dynamic Dashboard Router (Overview Mode vs. City Detail Mode)
# -----------------------------------------------------------------------------
if selected_city.startswith("None ("):
    render_overview(selected_state)
else:
    render_city_detail(selected_city, all_cities)

# -----------------------------------------------------------------------------
# 6. Architecture & System Design Drawer (Interview Q&A Guide)
# -----------------------------------------------------------------------------
st.markdown("---")
render_architecture_drawer()

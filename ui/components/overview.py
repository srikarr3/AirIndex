import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from ui.icons import svg_icon
from ui.data import (
    load_summary_for_scope,
    load_city_rankings,
    load_state_rankings
)

def render_overview(selected_state: str):
    """Renders the top-level Overview dashboard when no single city is selected."""
    summary_data = load_summary_for_scope(selected_state)
    
    avg_aqi = summary_data.get('avg_aqi', 0)
    peak_c = summary_data.get('peak_city', 'N/A')
    peak_aqi = summary_data.get('peak_aqi', 0)
    total_c = summary_data.get('total_cities', 0)
    total_st = summary_data.get('total_stations', 0)
    
    max_cpcb_raw = summary_data.get('max_cpcb_ts')
    max_cpcb_ist = (pd.to_datetime(max_cpcb_raw) + pd.Timedelta(hours=5, minutes=30)) if pd.notnull(max_cpcb_raw) else datetime.now()
    
    max_ing_raw = summary_data.get('max_ingested_at')
    max_ing_ist = (pd.to_datetime(max_ing_raw) + pd.Timedelta(hours=5, minutes=30)) if pd.notnull(max_ing_raw) else datetime.now()
    
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

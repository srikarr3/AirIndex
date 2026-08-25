import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from ui.icons import svg_icon
from ui.data import (
    load_latest_city_aqi,
    load_pollutant_concentrations,
    load_pollutant_subindices,
    load_latest_advisory,
    load_city_hourly_series,
    get_category_color
)

def render_city_detail(selected_city: str, all_cities: list):
    """Renders the detailed dashboard view for a specifically selected city."""
    latest_data = load_latest_city_aqi(selected_city)
    pollutants_map = load_pollutant_concentrations(selected_city)
    subindex_df = load_pollutant_subindices(selected_city)
    advisory_data = load_latest_advisory(selected_city)

    if latest_data is None:
        st.warning(f"No transformed hourly AQI records found for {selected_city} in database.")
        return

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
    ingested_ist = (pd.to_datetime(ingested_raw) + pd.Timedelta(hours=5, minutes=30)) if pd.notnull(ingested_raw) else datetime.now()
    
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
        with st.popover("ℹ️ Methodology & Disclaimers"):
            st.markdown("""
            **Cigarette Equivalence Methodology**:
            - Derived from the **Berkeley Earth** rule-of-thumb model: *1 cigarette ≈ 22 µg/m³ of PM₂.₅ over 24-hour continuous exposure*.
            - **Scientific Caveat**: This metric is an intuitive visual comparison for public risk communication. It compares mass concentration of fine particulates inhaled, but active cigarette smoking introduces distinct chemical carcinogens and heavy metals directly via high-temperature combustion.
            """)

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

    else:
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

    # --- City vs City Showdown ---
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

    # --- Annual Lung Dust Ingestion Calculator ---
    st.markdown("---")
    st.markdown(f"### 🫁 Annual Lung Dust Filtered Calculator — {selected_city}")
    st.caption("Human lungs inhale approximately ~11,000 Liters of air daily. Estimated particulate mass filtered per year:")

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

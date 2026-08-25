import streamlit as st

def apply_custom_theme():
    """Injects custom dark glassmorphic styling and responsive CSS rules into Streamlit app."""
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

        /* Equal-Height Glass Card Base */
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

        /* Pollutant Grid Cards */
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

        /* Category Badges */
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

        /* Health Advisory Box */
        .advisory-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border-left: 4px solid #818CF8;
            border-radius: 12px;
            padding: 1.25rem;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        /* Health Risk Cards */
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

        /* Recommendation Cards */
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

        /* Showdown Box */
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

        /* Architecture Expander styling */
        .arch-container {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(129, 140, 248, 0.3);
            border-radius: 12px;
            padding: 1.2rem;
            margin-top: 1.5rem;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid rgba(255, 255, 255, 0.06);
        }
    </style>
    """, unsafe_allow_html=True)

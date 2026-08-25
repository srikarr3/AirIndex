import streamlit as st

def render_header():
    """Renders the top banner and sub-header for AirIndex."""
    st.markdown('<div class="title-header">AirIndex India</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-Time Official CPCB Air Quality Index & Multi-Factor Intelligence System</div>', unsafe_allow_html=True)

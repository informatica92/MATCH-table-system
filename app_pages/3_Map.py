import streamlit as st

import os

import utils.streamlit_utils as stu

stu.add_title_text(st, frmt="{title}")

st.header("🗺️ Map")

gmap_url = os.environ.get('GMAP_MAP_URL')
if gmap_url:
    st.iframe(gmap_url, height=500)
else:
    st.warning("GMAP_MAP_URL environment variable not set")

with st.sidebar:
    stu.add_donation_button()

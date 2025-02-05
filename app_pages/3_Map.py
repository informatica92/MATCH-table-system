import streamlit as st

import os

import utils.streamlit_utils as stu

col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)

st.header("🗺️ Map")

gmap_url = os.environ.get('GMAP_MAP_URL')
if gmap_url:
    st.components.v1.iframe(gmap_url, height=500)
else:
    st.warning("GMAP_MAP_URL environment variable not set")


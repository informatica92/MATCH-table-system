import streamlit as st

import os

import utils.streamlit_utils as stu

st.title(f"{stu.get_title()}")
st.header("🗺️ Map")

gmap_url = os.environ.get('GMAP_MAP_URL')
if gmap_url:
    st.components.v1.iframe(gmap_url, height=500)
else:
    st.warning("GMAP_MAP_URL environment variable not set")


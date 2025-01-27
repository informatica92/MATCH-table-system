from importlib import import_module
import streamlit as st
from utils import streamlit_utils as stu

view_and_join_module = import_module('app_pages.1_View_&_Join')
if st.session_state.location_mode != "row":
    st.session_state.location_mode = "row"
    stu.refresh_table_propositions("Change Location Mode")

view_and_join_module.create_view_and_join_page()
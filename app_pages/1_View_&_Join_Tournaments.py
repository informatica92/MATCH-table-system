from importlib import import_module
import streamlit as st
from utils import streamlit_utils as stu

view_and_join_module = import_module('app_pages.1_View_&_Join_Base')
if st.session_state.location_mode != "default" or st.session_state.proposition_type_id_mode != 1:  # 0 = Proposition, 1 = Tournament, 2 = Demo
    st.session_state.location_mode = "default"
    st.session_state.proposition_type_id_mode = 1
    stu.refresh_table_propositions("Loading Tournament page")

view_and_join_module.create_view_and_join_page()

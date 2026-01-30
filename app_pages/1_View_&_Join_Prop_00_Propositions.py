from importlib import import_module
import streamlit as st
from utils import streamlit_utils as stu
from utils.table_system_proposition import StreamlitTablePropositions

view_and_join_module = import_module(stu.VIEW_JOIN_BASE_MODULE)
if st.session_state.location_mode is not None or st.session_state.proposition_type_id_mode != 0:  # 0 = Proposition, 1 = Tournament, 2 = Demo
    st.session_state.location_mode = None
    st.session_state.proposition_type_id_mode = 0
    StreamlitTablePropositions.refresh_table_propositions("Loading Proposition page")

view_and_join_module.create_view_and_join_page()

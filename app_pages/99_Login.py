import streamlit as st

import utils.streamlit_utils as stu
from utils.table_system_user import login_button


col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)


with st.container(border=True, key="login_container"):
    st.subheader("Login")
    login_button()
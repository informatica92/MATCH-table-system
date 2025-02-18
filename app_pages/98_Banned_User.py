import streamlit as st

import utils.streamlit_utils as stu


col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
# stu.add_help_button(col_help)

col_fake1, col_login, col_fake2 = st.columns([2, 4, 2])
with col_login:
    with st.container(border=True, key="login_container"):
        st.subheader("❌ You are a banned user")
        st.write("You have been banned from the app")
        st.write("Please contact the admin for more information")
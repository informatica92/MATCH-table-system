import streamlit as st

import utils.streamlit_utils as stu
from utils.table_system_user import login_button


col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)

col_fake1, col_login, col_fake2 = st.columns([2, 4, 2])
with col_login:
    with st.container(border=True, key="login_container"):
        st.subheader("Login")
        st.write("Please login to access the app")
        st.write("You can login with your **Auth0** account or with your **Google** account. \n\n"
                 "If you don't have an account, you can create one by clicking on the **'Sign up'** link. \n\n"
                 "Once you are logged in, you will be able to access the app pages. \n\n"
                 "Anyway, **in order to also create, join, edit and delete tables, you also need to set a username**")
        login_button()
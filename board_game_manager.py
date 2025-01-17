import streamlit as st
import os

import utils.streamlit_utils as stu
from utils.table_system_user import StreamlitTableSystemUser, login_button, logout_button

# # FEATURES

# # IMPROVEMENTS
# TODO: add expansions into list and dataframe view
# TODO: use @st.fragments
# TODO: replace text+bgg search with: https://pypi.org/project/streamlit-searchbox/ (st.link_button) (requires no streamlit_extras => no cookies)

st.session_state['user'] = StreamlitTableSystemUser(init_session_state_for_username=True)

if st.session_state.user.is_logged_in():
    pg = st.navigation(
        [
            st.Page("app_pages/1_View_&_Join.py", icon="📜", default=True),
            st.Page("app_pages/2_Create.py", icon="➕"),
            st.Page("app_pages/3_Map.py", icon="🗺️"),
            st.Page("app_pages/4_User.py", icon="👦🏻")
        ]
    )
else:
    pg = st.navigation(
        [
            st.Page("app_pages/99_Login.py", icon="🔐", default=True)
        ]
    )

st.set_page_config(page_title=stu.get_title(), layout="wide", page_icon="🎴")

st.markdown(stu.BOUNCE_SIDEBAR_ICON, unsafe_allow_html=True)


# Initialize propositions in session state
if "propositions" not in st.session_state:
    print("Initializing st.session_state.propositions")
    stu.refresh_table_propositions("Init")

# Initialize god_mode in session state
if "god_mode" not in st.session_state:
    st.session_state['god_mode'] = False


# Add a username setting in the sidebar
with (st.sidebar):
    # LOGOs section
    if not os.environ.get('LOGO_LARGE'):
        st.logo(stu.get_logo(), size="large")
    else:
        st.logo(os.environ.get('LOGO_LARGE'), icon_image=stu.get_logo())  # can't use the 'size' here since it only works with the icon

    # LOGIN and LOGOUT section
    with st.container(border=True):
        col_login, col_logout = st.columns([1, 1])
        with col_login:
            login_button()
        with col_logout:
            logout_button()
        # User and username section
        if st.session_state.user.is_logged_in():
            if st.session_state['username']:
                st.info(f"Welcome back, **{st.session_state['username']}**\n\n*Use the User page to edit your username*")
            else:
                st.warning("Set a username to join tables.\n\nUse the User page to edit your username")

    if st.session_state.user.is_logged_in():
        # GOD MODE section
        with st.expander("🔒 God Mode"):
            god_mode_is_active = st.toggle("God Mode", key="god_mode", value=False, disabled=not st.session_state.user.is_admin)
            if st.session_state.user.is_admin:
                if god_mode_is_active:
                    st.warning("God Mode is **active**. You can do anything you want. Be careful!")
                else:
                    st.info("God Mode is **disabled**. You can only act as a normal user now")

pg.run()

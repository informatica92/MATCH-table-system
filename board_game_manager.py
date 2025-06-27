import streamlit as st
import os

import utils.streamlit_utils as stu
from utils.table_system_user import StreamlitTableSystemUser, login_button, logout_button

# # FEATURES
# TODO: replace text+bgg search with: https://pypi.org/project/streamlit-searchbox/ (requires no streamlit_extras => no cookies)
# TODO: add board game image during creation (for check)
# # IMPROVEMENTS
# TODO: use @st.fragments
# TODO: optimize return data in BGG info (from tuple to dataclass)
# TODO: SQC: duration should be float4 (so it can be 0.5hours, 1.5hours, etc.) or minutes
# TODO: SQC: redirect to created table once done
# TODO: SQC: sidebar button more visible


st.set_page_config(page_title=stu.get_title(), layout="wide", page_icon="🎴")

st.session_state['user'] = StreamlitTableSystemUser(init_session_state_for_username=True)

if st.session_state['user'].is_banned:
    # If the user is banned, show ONLY the banned page
    pg = st.navigation(
        [
            st.Page("app_pages/98_Banned_User.py", icon="❌", default=True)
        ]
    )
    pg.run()
    st.stop()
    ###################################################################################################################

# ...alternatively, show the normal pages
def_loc = stu.get_default_location()
def_loc_alias = def_loc['alias']

view_and_join_loc_pages = [
    st.Page(stu.VIEW_JOIN_LOC_DEFAULT_PAGE, icon="📜", default=True, title=def_loc_alias),
    st.Page(stu.VIEW_JOIN_LOC_ROW_PAGE, icon="🌍", title=stu.get_rest_of_the_world_page_name(), url_path="restoftheworld"),
]

view_and_join_prop_pages = [
    st.Page(stu.VIEW_JOIN_PROPOSITIONS_PAGE, icon="🎴", title="Propositions", url_path="propositions"),
]

if stu.str_to_bool(os.getenv('CAN_ADMIN_CREATE_TOURNAMENT')):
    view_and_join_prop_pages.append(
        st.Page(stu.VIEW_JOIN_TOURNAMENTS_PAGE, icon="⚔️", title="Tournaments", url_path="tournaments")
    )
if stu.str_to_bool(os.getenv('CAN_ADMIN_CREATE_DEMO')):
    view_and_join_prop_pages.append(
        st.Page(stu.VIEW_JOIN_DEMOS_PAGE, icon="🎁", title="Demos", url_path="demos")
    )

other_pages = [
    st.Page(stu.CREATE_PAGE, icon="➕"),
    st.Page(stu.MAP_PAGE, icon="🗺️"),
    st.Page(stu.USER_PAGE, icon="👦🏻")
]

pg = st.navigation(
    {
        "Locations": view_and_join_loc_pages,
        "Propositions": view_and_join_prop_pages,
        "Other": other_pages
    }
)

st.markdown(stu.BOUNCE_SIDEBAR_ICON, unsafe_allow_html=True)

# Initialize location_mode in session state
if "location_mode" not in st.session_state:
    st.session_state['location_mode'] = None

if "proposition_type_id_mode" not in st.session_state:
    st.session_state['proposition_type_id_mode'] = None  # 0 = Proposition, 1 = Tournament, 2 = Demo

# Initialize propositions in session state
if "propositions" not in st.session_state:
    # print("Initializing st.session_state.propositions")
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
        else:
            st.warning("**Log in** to **join** and **create** tables.")

    if st.session_state.user.is_admin:
        # GOD MODE section
        with st.expander(":lock_with_ink_pen: God Mode"):
            god_mode_is_active = st.toggle("God Mode", key="god_mode", value=False, disabled=not st.session_state.user.is_admin)
            if st.session_state.user.is_admin:
                if god_mode_is_active:
                    st.warning("God Mode is **active**. You can do anything you want. Be careful!")
                else:
                    st.info("God Mode is **disabled**. You can only act as a normal user now")

pg.run()

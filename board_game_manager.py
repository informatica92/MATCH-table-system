import streamlit as st
import os

import utils.streamlit_utils as stu
from utils.table_system_user import StreamlitTableSystemUser

# # FEATURES
# TODO: use multi_pages -> https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app
# TODO: use st.cache_data for bgg info
# TODO: add "location" (system or user) into the Create (system locations => no user id)
# # IMPROVEMENTS
# TODO: use @st.fragments
# TODO: replace text+bgg search with: https://pypi.org/project/streamlit-searchbox/ (st.link_button) (requires no streamlit_extras => no cookies)
# TODO: link user table to joined_players and table_propositions
#   TODO: joined_players table -> change player_name to FK to users.id
#   TODO: change the get_table_propositions query to keep the same structure but joining now joined_players and users
#   TODO: table_propositions table -> change proposed_by to FK to users.id
#   TODO: change the leave_table to remove row using user_id instead of player_name
#   TODO: change the join_table to add row using user_id instead of player_name

pg = st.navigation(
    [
        st.Page("pages/1_View_&_Join.py", icon="📜", default=True),
        st.Page("pages/2_Create.py", icon="➕"),
        st.Page("pages/3_Map.py", icon="🗺️"),
        st.Page("pages/4_User.py", icon="👦🏻")
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


st.session_state['user'] = StreamlitTableSystemUser(init_session_state_for_username=True)

# Add a username setting in the sidebar
with (st.sidebar):
    if not os.environ.get('LOGO_LARGE'):
        st.logo(stu.get_logo(), size="large")
    else:
        st.logo(os.environ.get('LOGO_LARGE'),icon_image=stu.get_logo())  # can't use the 'size' here since it only works with the icon
    if st.session_state['username']:
        st.info(f"Welcome back, **{st.session_state['username']}**\n\n*Use the User page to edit your username*")
    else:
        st.warning("Set a username to join tables.\n\nUse the User page to edit your username")
    with st.expander("🔒 God Mode"):
        god_mode_is_active = st.toggle("God Mode", key="god_mode", value=False, disabled=not st.session_state.user.is_admin)
        if st.session_state.user.is_admin:
            if god_mode_is_active:
                st.warning("God Mode is **active**. You can do anything you want. Be careful!")
            else:
                st.info("God Mode is **disabled**. You can only act as a normal user now")

pg.run()

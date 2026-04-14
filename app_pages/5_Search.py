import streamlit as st
import pandas as pd
import utils.streamlit_utils as stu
from utils.bgg_manager import get_user_collection, clear_user_collection_cache
from utils.table_system_user import login_button


stu.add_title_text(st, frmt="{title}")

if not st.session_state.user.is_logged_in():
    col_fake1, col_login, col_fake2 = st.columns([2, 4, 2])
    with col_login:
        with st.container(border=True, key="login_container"):
            st.subheader("🛡️ Login")
            st.write("Please login to access the app")
            st.write("You can login with your **Auth0** account or with your **Google** account. \n\n"
                     "If you don't have an account, you can create one by clicking on the **'Sign up'** link. \n\n"
                     "Once you are logged in, you will be able to access the app pages. \n\n"
                     "Anyway, **in order to also Create**, **Join**, **Edit** and **Delete** tables, **you also need to "
                     "set an Username** (the app will guide you in doing this)")
            login_button()
    st.stop()

bgg_usernames = stu.get_all_bgg_usernames()
collections = []
num_bgg_usernames = len(bgg_usernames)

if st.button("🧹 Clear Cache"):
    clear_user_collection_cache()

progress_bar = st.progress(text="Processing", value=0)
for i, bgg_username in enumerate(bgg_usernames):
    progress_bar.progress((i + 1) / num_bgg_usernames, text=bgg_username)
    collections.extend(get_user_collection(bgg_username))
progress_bar.empty()

collections_df = pd.DataFrame(collections)

with st.container(horizontal=True):
    st.multiselect(options=collections_df.username.unique(), key="search_game_by_username", label="Search by username")
    st.multiselect(options=collections_df.name.unique(), key="search_game_by_name", label="Search by game name", max_selections=1)

if st.session_state.search_game_by_username:
    collections_df = collections_df[collections_df.username.isin(st.session_state.search_game_by_username)]

if st.session_state.search_game_by_name:
    collections_df = collections_df[collections_df.name.isin(st.session_state.search_game_by_name)]

column_config = {
    "thumb": st.column_config.ImageColumn(width="small"),
    "name": st.column_config.TextColumn(width="large")
}
st.dataframe(collections_df, column_config=column_config, row_height=50)

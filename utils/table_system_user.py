from utils.sql_manager import SQLManager
import streamlit as st

@st.cache_data(ttl="1h")  # cache user_id, username, is_admin from email but only for 1h
def _get_or_create_user(email):
    print(f"Getting user info [no cache] for {st.experimental_user.email}")
    sql_manager = SQLManager()
    user_id, username, is_admin = sql_manager.get_or_create_user(email)
    return user_id, username, is_admin

class StreamlitTableSystemUser(object):
    def __init__(self, init_session_state_for_username=True):
        """
        A class to manage user authentication and username updates in a Streamlit application.

        This class handles user creation, retrieval, and username updates using SQLManager.
        It integrates with Streamlit's experimental user authentication and session state.

        attributes:
            sql_manager (SQLManager): Instance of SQLManager for database operations
            email (str): Email of the authenticated user from Streamlit from [experimental_]user
            user_id (int): Database ID of the user
            username (str): Username of the user
            is_admin (bool): Admin status of the user

        params:
            init_session_state_for_username (bool): Whether to initialize the session state for username
        """
        self.sql_manager = SQLManager()
        self.email = st.experimental_user.email

        self.user_id, self.username, self.is_admin = _get_or_create_user(self.email)
        if init_session_state_for_username:
            st.session_state.username = self.username

    def update_username(self):
        if len(st.session_state.username_user_setting or "") < 3:
            print(f"Error updating username: Username must be at least 3 characters long")
            st.session_state.update_username_from_user_error = "Username must be at least 3 characters long"
            return
        try:
            print(f"Updating username from {st.session_state.username} to {st.session_state.username_user_setting}")
            self.sql_manager.set_username(self.email, st.session_state.username_user_setting)
            print(f"Clearing cache for {self.email}")
            _get_or_create_user.clear(self.email)
            # st.session_state.username = st.session_state.username_user_setting
        except AttributeError as e:
            print(f"Error updating username: {e}")
            st.session_state.update_username_from_user_error = e
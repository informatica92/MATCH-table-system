from utils.sql_manager import SQLManager
import streamlit as st

from utils.table_system_logging import logging

def login_button():
    if st.button("🔐 Login", width='stretch', disabled=st.session_state.user.is_logged_in()):
        st.login(provider="auth0")

def logout_button():
    if st.button("❌ Logout", width='stretch', disabled=not st.session_state.user.is_logged_in()):
        st.logout()

@st.cache_data(ttl="1h")  # cache user_id, username, is_admin from email but only for 1h
def _get_or_create_user(email):
    if email:
        logging.info(f"Getting user info [no cache] for {st.user.email}")
        sql_manager = SQLManager()
        user_id, username, name, surname, bgg_username, telegram_username, is_admin, is_banned = sql_manager.get_or_create_user(email)
        return user_id, username, name, surname, bgg_username, telegram_username, is_admin, is_banned
    else:
        return None, None, None, None, None, None, None, None

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
            name (str): First name of the user
            surname (str): Last name of the user
            bgg_username (str): BGG username of the user
            telegram_username (str): Telegram username of the user
            is_admin (bool): Admin status of the user

        params:
            init_session_state_for_username (bool): Whether to initialize the session state for username
        """
        self.sql_manager = SQLManager()
        self.email = st.user.get("email")

        (
            self.user_id,
            self.username,
            self.name,
            self.surname,
            self.bgg_username,
            self.telegram_username,
            self.is_admin,
            self.is_banned
        ) = _get_or_create_user(self.email)

        if init_session_state_for_username:
            st.session_state.username = self.username

    def update_user(self):
        if len(st.session_state.username_user_setting or "") < 3:
            logging.error(f"Error updating username: Username must be at least 3 characters long")
            st.session_state.update_username_from_user_error = "Username must be at least 3 characters long"
            return
        try:
            logging.info(f"Updating username from {st.session_state.username} to {st.session_state.username_user_setting}")
            self.sql_manager.set_user(
                email=self.email,
                username=st.session_state.username_user_setting,
                name=st.session_state.name_user_setting,
                surname=st.session_state.surname_user_setting,
                bgg_username=st.session_state.bgg_username_user_setting,
                telegram_username=st.session_state.telegram_username_user_setting
            )
            logging.info(f"Clearing cache for {self.email}")
            _get_or_create_user.clear(self.email)
            # st.session_state.username = st.session_state.username_user_setting
        except AttributeError as e:
            logging.error(f"Error updating username: {e}")
            st.session_state.update_username_from_user_error = e

    def is_logged_in(self):
        return self.email is not None

    def __str__(self):
        """
        returns "<email> (<user_id>)"

        email and user_id can also be None in case of non-authenticated users
        :return: email (user_id)
        """
        return f"{self.email} ({self.user_id})"

import streamlit as st

import utils.streamlit_utils as stu
from utils.telegram_notifications import get_telegram_profile_page_url
from utils.bgg_manager import get_bgg_profile_page_url


col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)

st.subheader("User settings")

col1, col2 = st.columns([1, 4])
col1.text_input("User ID", value=st.session_state.user.user_id, disabled=True)
col2.text_input("Email", value=st.session_state.user.email, disabled=True)
with st.form("user_setting_form", border=False):
    # if username is none, warn the user to set the username
    if not st.session_state.username:
        st.warning("You need to **set a Username** below to **join** and **create** tables. ⤵️")
    st.text_input("Username", value=st.session_state.username, key="username_user_setting", disabled=False, placeholder="[Mandatory] Set a username")

    col_name, col_surname =  st.columns([1, 1])
    col_name.text_input("Name", value=st.session_state.user.name, key="name_user_setting", disabled=False, placeholder="[Optional] Set your name")
    col_surname.text_input("Surname",  value=st.session_state.user.surname, key="surname_user_setting", disabled=False, placeholder="[Optional] Set your surname")

    col_bgg_username, col_telegram_username =  st.columns([1, 1])
    col_bgg_username.text_input("BGG username",  value=st.session_state.user.bgg_username, key="bgg_username_user_setting", disabled=False, placeholder="[Optional] Set your BGG username")
    with col_bgg_username:
        if st.session_state.user.bgg_username:
            stu.st_write(get_bgg_profile_page_url(st.session_state.user.bgg_username, as_html_link=True))
        else:
            stu.st_write("No BGG username set, set it to test the link")
    col_telegram_username.text_input("Telegram username (without the '@')", value=st.session_state.user.telegram_username, key="telegram_username_user_setting", disabled=False, placeholder="[Optional] Set your Telegram username")
    with col_telegram_username:
        if st.session_state.user.telegram_username:
            stu.st_write(get_telegram_profile_page_url(st.session_state.user.telegram_username, as_html_link=True))
        else:
            stu.st_write("No Telegram username set, set it to test the link")

    if st.form_submit_button("💾 Update ", on_click=st.session_state.user.update_user):
        if not st.session_state.get("update_username_from_user_error"):
            new_user_details =\
                f"\t- Username: {st.session_state.username_user_setting},\n"\
                f"\t- Name: {st.session_state.name_user_setting},\n"\
                f"\t- Surname: {st.session_state.surname_user_setting},\n"\
                f"\t- BGG username: {st.session_state.bgg_username_user_setting},\n"\
                f"\t- Telegram username: {st.session_state.telegram_username_user_setting}\n"

            st.success(f"User updated successfully:\n\n{new_user_details}")
            stu.refresh_table_propositions("User update")
        else:
            st.error(f"Error updating username: {st.session_state.update_username_from_user_error}")
        st.session_state["update_username_from_user_error"] = None

st.subheader("User Admin")
st.toggle("Admin", value=st.session_state.user.is_admin, disabled=True, help="Ask the admin to change this setting for your user")
if st.session_state.user.is_admin:
    stu.manage_user_locations(user_id=None)

st.subheader("User locations")
stu.st_write("Use the following list to manage your locations. Having one or more registered location will allow "
             "you to specify where a table proposition will take place, apart from the DEFAULT location <br>"
             "The DEFAULT location is automatically generated. <br>"
             "Also, removing a location will set the location of all tables at that location to <i>'Unknown'</i> and "
             "the corresponding tables will be available into the 'Rest of the World' page. <br>")
stu.manage_user_locations(user_id=st.session_state.user.user_id)
stu.st_write("Using <b>'Locations'</b> you automatically accept the "
             "<a href='https://github.com/informatica92/MATCH-table-system/tree/main/static/gdpr'>GDPR policy</a> "
             "of this application")


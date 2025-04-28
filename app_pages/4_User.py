import streamlit as st

import utils.streamlit_utils as stu
from utils.telegram_notifications import get_telegram_profile_page_url
from utils.bgg_manager import get_bgg_profile_page_url
from utils.table_system_user import login_button


col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)

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

st.subheader("User settings")

col1, col2 = st.columns([1, 4])
col1.text_input("User ID", value=st.session_state.user.user_id, disabled=True)
col2.text_input("Email", value=st.session_state.user.email, disabled=True)
with st.form("user_setting_form", border=False):
    # if username is none, warn the user to set the username
    if not st.session_state.username:
        st.warning("You need to **set a Username** below to **join** and **create** tables. ⤵️")
    username_markdown = "Username" if st.session_state.username else ":red[Username]"
    st.text_input(username_markdown, value=st.session_state.username, key="username_user_setting", disabled=False, placeholder="[Mandatory] Set a username")

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
    st.subheader("Admin locations (visible only to admins)")
    stu.st_write(f"Use the following list to manage admin locations. <br>"
                 f"This lists differs from the \"User locations\", below, since <b>\"Admin locations\" are visible to "
                 f"all users</b> while \"User locations\" are only visible to the user who created them. <br>")
    stu.manage_user_locations(user_id=None)

st.subheader("User locations")
stu.st_write(f"Use the following list to manage your locations. Having one or more registered location will allow "
             f"you to specify where a table proposition will take place, apart from the DEFAULT location <br>"
             f"The DEFAULT location is automatically generated. <br>"
             f"Also, removing a location will set the location of all tables at that location to <i>'Unknown'</i> and "
             f"the corresponding tables will be available into the '{stu.get_rest_of_the_world_page_name()}' page. <br>")
stu.manage_user_locations(user_id=st.session_state.user.user_id)
stu.st_write("Using <b>'Locations'</b> you automatically accept the "
             "<a href='https://github.com/informatica92/MATCH-table-system/tree/main/static/gdpr'>GDPR policy</a> "
             "of this application")


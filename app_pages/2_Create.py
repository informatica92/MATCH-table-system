import streamlit as st
from datetime import datetime
import os

import utils.streamlit_utils as stu
from utils.bgg_manager import search_bgg_games, get_bgg_game_info

# redirect to "User" page if username is not set
stu.redirect_to_user_page_if_username_not_set()

col_title, col_help = st.columns([9, 1])
stu.add_title_text(col_title, frmt="{title}")
stu.add_help_button(col_help)

st.header("➕ Create a New Table Proposition")

game_name = st.text_input("Search for Game Name")
stu.st_write("Write a game name in the above text box and press ENTER. The matching games from BGG will appear here:")
bgg_game_id = None

try:
    matching_games = search_bgg_games(game_name)
except AttributeError as e:
    st.error(f"Error searching for games: {e}")
    matching_games = []

selected_game = st.selectbox("Select the matching game", matching_games, format_func=lambda x: x[1])
stu.st_write("Select the matching game from BGG for auto detecting information like the board game image")
if selected_game:
    bgg_game_id = selected_game[0]

image_url, game_description, categories, mechanics, available_expansions = None, None, [], [], []
if bgg_game_id:
    st.write(f"Selected BGG Game ID: {bgg_game_id}")
    image_url, game_description, categories, mechanics, available_expansions, _ = get_bgg_game_info(bgg_game_id)

if st.session_state.user.is_admin:
    # Selection of the Proposition Type
    st.divider()

    st.selectbox("Proposition Type", options=stu.get_table_proposition_types(as_list_of_dicts=True), key="proposition_type", format_func=lambda x: x["value"])
    stu.st_write(f"Selecting a Type different from \"Proposition\" this will disable location selection")
    # st.write(st.session_state.proposition_type)

    st.divider()

with st.form(key="create_new_proposition_form", border=False):

    # expansions selector
    expansions_to_adopt = st.multiselect("Select expansions", available_expansions, key="expansions", format_func=lambda x: x['value'])

    # number of players and duration
    col1, col2 = st.columns([1, 1])
    with col1:
        st.number_input("Max Number of Players", min_value=1, max_value=100, step=1, key="max_players")
    with col2:
        st.number_input("Duration (in hours)", min_value=1, max_value=24, step=1, key="duration")

    # date and time
    col1, col2 = st.columns([1, 1])
    with col1:
        # get the optional default date from the environment variable, otherwise it will be set to the current date
        default_date = datetime.strptime(os.environ.get('DEFAULT_DATE', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        date_time = st.date_input("Date", value=default_date if default_date>datetime.now() else datetime.now(), key="date", min_value="today")
    with col2:
        # OLD version with granular time selection:
        # time = st.time_input("Time", step=60*30, key="time")
        # NEW version with Morning, Afternoon, Evening and Night
        time_options = ["09:00 - Morning", "14:00 - Afternoon", "18:00 - Evening", "22:00 - Night"]
        time_option = st.selectbox("Time Slot", options=time_options, key="time_option", help="Choose a time slot, you can change it in a more granular way once created, using '🖋️Edit'")
        time = stu.time_option_to_time(time_option)

    # locations
    can_users_set_location = stu.str_to_bool(os.getenv('CAN_USERS_SET_LOCATION', 'False'))
    if can_users_set_location and st.session_state.get("proposition_type", {}).get("id") == 0:
        locations = stu.get_available_locations(st.session_state.user.user_id)
    else:
        locations = [list(stu.get_default_location().values())]
    # 'id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id'
    locations = [(loc[0], loc[5]) for loc in locations]  # id, alias
    st.selectbox("Location", options=locations, key="location", format_func=lambda x: x[1])
    def_loc_alias = stu.get_default_location()['alias']
    code_html_style = "style='color: black; background-color: #f0f0f0;font-weight: bold;'"
    stu.st_write(f"Selecting <b>{def_loc_alias}</b> as location, the table will be displayed into the "
                 f"<code {code_html_style}>View & Join/📜{def_loc_alias}</code> page, otherwise you'll find it into the "
                 f"<code {code_html_style}>View & Join/🌍Rest of the World</code> page")
    if not can_users_set_location:
        stu.st_write("ℹ️ User locations are not displayed at the moment. <i>(CAN_USERS_SET_LOCATION set to False)</i>")

    # notes
    st.text_area("Notes", key="notes")

    st.checkbox("Join me by default to this table once created", key="join_me_by_default", value=True)
    stu.st_write("By default, you'll be added to this table once created. To avoid this, disable the above option")

    if st.session_state['username']:
        if bgg_game_id:
            if st.form_submit_button("Create Proposition", on_click=stu.create_callback, args=[selected_game[1] if selected_game else None, bgg_game_id, image_url]):
                st.success(f"Table proposition created successfully: {selected_game[1]} - {date_time} {time.strftime('%H:%M')}")
                if st.session_state.join_me_by_default:
                    st.success(f"You have also joined this table by default as {st.session_state.username}.")
        else:
            st.form_submit_button("Create Proposition", disabled=True)
            st.warning("Select a game from the list to create a proposition.")
    else:
        st.form_submit_button("Create Proposition", disabled=True)
        if st.session_state.user.is_logged_in():
            st.warning("Set a username to create a proposition.")
        else:
            st.warning("**Log in** to create a proposition.")


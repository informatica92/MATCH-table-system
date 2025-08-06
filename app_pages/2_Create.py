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

st.header("➕ Create Proposition")
image_url, game_description, categories, mechanics, available_expansions = None, None, [], [], []
if st.toggle("BGG Games", value=True, key="bgg_or_custom_game", help="Select if you want to search for a game on BGG or create a custom game proposition"):
    game_name = st.text_input("✍🏻 Search for Game Name")
    stu.st_write("Write a game name in the above text box and press ENTER. The matching games from BGG will appear here:")
    bgg_game_id = None

    try:
        matching_games = search_bgg_games(game_name)
    except AttributeError as e:
        st.error(f"Error searching for games: {e}")
        matching_games = []

    selected_game = st.selectbox(":material/checklist_rtl: Select the matching game", matching_games, format_func=lambda x: x[1])
    st.write("Now, select the matching game from BGG for auto detecting information like the board game image")
    if selected_game:
        bgg_game_id = selected_game[0]

    if bgg_game_id:
        image_url, game_description, categories, mechanics, available_expansions, _ = get_bgg_game_info(bgg_game_id)
        col1, col2 = st.columns([1, 4])
        col1.image(image_url,use_container_width=True)
        col2.caption(f"**Description**: {game_description[:300]}...")
        with col2:
            stu.st_write(f"<b>BGG URL</b>: <a href='{stu.get_bgg_url(bgg_game_id)}'>{stu.get_bgg_url(bgg_game_id)}</a>")
            stu.st_write(f"<b>Categories:</b> {', '.join(categories)}<br><b>Mechanics:</b> {', '.join(mechanics)}")
else:
    st.write("**Custom Game**: You can create a custom game proposition without searching BGG.")
    bgg_game_id = None
    selected_game = None
    st.text_input("✍🏻 Custom Game Name", key="custom_game_name", help="Enter the name of the custom game you want to create a proposition for.", placeholder="Custom Game (2025)")
    col_img, col_details = st.columns([1, 4])
    col_details.text_input("🖼️ Image URL", key="custom_image_url", help="Enter the URL of the image for the custom game. If not provided, a default image will be used.", placeholder="https://example.com/image.jpg")
    col_details.text_area("📝 Description", key="custom_game_description", help="Enter a description for the custom game. This will be used in the proposition details.", max_chars=120, placeholder="A brief description of the custom game.")
    col1, col2 = col_details.columns([1, 1])
    col1.text_input("📦 Categories (comma-separated)", key="custom_game_categories", help="Enter categories for the custom game, separated by commas.", max_chars=100, placeholder="Strategy, Card Game")
    col2.text_input("⚙️ Mechanics (comma-separated)", key="custom_game_mechanics", help="Enter mechanics for the custom game, separated by commas.", max_chars=100, placeholder="Deck Building, Worker Placement")
    try:
        col_img.image(st.session_state.get('custom_image_url') or stu.DEFAULT_IMAGE_URL, use_container_width=True)
    except Exception as e:
        col_img.error(f"Error loading image: {e}")

st.divider()

if st.session_state.user.is_admin:
    # Selection of the Proposition Type
    st.selectbox("🤌🏻 Proposition Type", options=stu.get_table_proposition_types(as_list_of_dicts=True), key="proposition_type", format_func=lambda x: x["value"])
    st.divider()

with st.form(key="create_new_proposition_form", border=False):

    # expansions selector
    expansions_to_adopt = st.multiselect(":package: Select expansions", available_expansions, key="expansions", format_func=lambda x: x['value'])

    # number of players and duration
    col1, col2 = st.columns([1, 1])
    with col1:
        st.number_input(":material/groups: Max Number of Players", min_value=1, max_value=100, step=1, key="max_players")
    with col2:
        st.number_input(f":hourglass: Duration (in minutes, step: {stu.get_duration_step()}mins)", min_value=30, max_value=24*60, step=stu.get_duration_step(), key="duration", value=60)

    # date and time
    col1, col2 = st.columns([1, 1])
    with col1:
        # get the optional default date from the environment variable, otherwise it will be set to the current date
        default_date = datetime.strptime(os.environ.get('DEFAULT_DATE', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        date_time = st.date_input(":date: Date", value=default_date if default_date>datetime.now() else datetime.now(), key="date", min_value="today")
    with col2:
        # OLD version with granular time selection:
        # time = st.time_input("Time", step=60*30, key="time")
        # NEW version with Morning, Afternoon, Evening and Night
        time_options = ["09:00 - Morning", "14:00 - Afternoon", "18:00 - Evening", "22:00 - Night"]
        time_option = st.selectbox(":watch: Time Slot", options=time_options, key="time_option", help="Choose a time slot, you can change it in a more granular way once created, using '🖋️Edit'")
        time = stu.time_option_to_time(time_option)

    # locations
    can_users_set_location = stu.str_to_bool(os.getenv('CAN_USERS_SET_LOCATION', 'False'))
    if can_users_set_location:
        locations = stu.get_available_locations(st.session_state.user.user_id, True, False)
    else:
        locations = [list(stu.get_default_location().values())]
    # 'id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id'
    locations = [(loc[0], loc[5]) for loc in locations]  # id, alias
    st.selectbox(":world_map: Location", options=locations, key="location", format_func=lambda x: x[1])
    def_loc_alias = stu.get_default_location()['alias']
    stu.st_write(f"Selecting <b>{def_loc_alias}</b> as location, the table will be displayed into the "
                 f"<b>''📜{def_loc_alias}''</b> page, otherwise you'll find it into the "
                 f"<b>''🌍{stu.get_rest_of_the_world_page_name()}''</b> page")
    if not can_users_set_location:
        stu.st_write("ℹ️ User locations are not displayed at the moment. <i>(CAN_USERS_SET_LOCATION set to False)</i>")

    # notes
    st.text_area(":black_nib: Notes", key="notes")

    st.checkbox("Join me by default to this table once created", key="join_me_by_default", value=True)
    stu.st_write("By default, you'll be added to this table once created. To avoid this, disable the above option")

    if st.session_state['username']:
        if bgg_game_id or st.session_state.get('custom_game_name', True):
            if bgg_game_id:
                selected_game_name = selected_game[1] if selected_game else None
            else:
                selected_game_name = st.session_state.get('custom_game_name', None)
                bgg_game_id = None
                image_url = st.session_state.get('custom_image_url', None)
            if st.form_submit_button("Create Proposition", on_click=stu.create_callback, args=[selected_game_name, bgg_game_id, image_url]):
                st.success(f"Table proposition created successfully: {selected_game_name} - {date_time} {time.strftime('%H:%M')}")
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

with st.sidebar:
    stu.add_donation_button()
import streamlit as st

from time import time as time_time
from datetime import datetime
import os

import utils.streamlit_utils as stu
from utils.telegram_notifications import get_telegram_profile_page_url
from utils.bgg_manager import search_bgg_games, get_bgg_game_info, get_bgg_url, get_bgg_profile_page_url
from utils.altair_manager import timeline_chart
from utils.table_system_user import StreamlitTableSystemUser

# # FEATURES
# TODO: create user entity and link user id into joined_player table
# TODO: use multi_pages -> https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app
# TODO: if no streamlit_extras => use the select_box in Create
# TODO: use st.cache_data for bgg info
# TODO: add logo(s) instead of image into the sidebar
# # IMPROVEMENTS
# TODO: use @st.fragments
# TODO: replace text+bgg search with: https://pypi.org/project/streamlit-searchbox/ (st.link_button)
# TODO: joined_players table -> change player_name to FK to users.id
# TODO: change the get_table_propositions query to keep the same structure but joining now joined_players and users
# TODO: table_propositions table -> change proposed_by to FK to users.id
# TODO: change the leave_table to remove row using user_id instead of player_name
# TODO: change the join_table to add row using user_id instead of player_name

st.set_page_config(page_title=stu.get_title(), layout="wide")

st.markdown(stu.BOUNCE_SIDEBAR_ICON, unsafe_allow_html=True)



@st.dialog("🖋️ Edit Table")
def dialog_edit_table_proposition(table_id, old_name, old_max_players, old_date, old_time, old_duration, old_notes, old_bgg_game_id, joined_count):
    with st.form(key=f"form-edit-{table_id}"):
        col1, col2 = st.columns([1, 1])
        with col1:
            game_name = st.text_input("Game Name", value=old_name, disabled=True)
            max_players = st.number_input("Max Players", value=old_max_players, step=1, min_value=joined_count)
            date = st.date_input("Date", value=old_date)
        with col2:
            bgg_game_id = st.text_input("BGG Game ID", value=old_bgg_game_id, help=stu.BGG_GAME_ID_HELP, disabled=True)
            duration = st.number_input("Duration (hours)", value=old_duration, step=1)
            time = st.time_input("Time", value=old_time, step=60*30)
        notes = st.text_area("Notes", value=old_notes)

        submitted = st.form_submit_button("💾 Update")
        if submitted:
            stu.update_table_propositions(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id)
            st.rerun()

@st.dialog("⛔ Delete Proposition")
def dialog_delete_table_proposition(table_id: int, game_name: str, joined_count: int, joined_players: list, proposed_by:str):
    with st.form(key=f"form-delete-{table_id}"):
        st.write(f"Please, confirm you want to delete Table {table_id}:")
        st.write(f"**{game_name}**")

        if joined_count:
            joined_players_markdown = '\n\t - '  + '\n\t - '.join(joined_players)
            st.write(f"Details:\n "
                     f"- proposed by **{proposed_by}**\n "
                     f"- with {joined_count} player(s): {joined_players_markdown}\n ")
        else:
            st.write(f"Details:\n "
                     f"- proposed by **{proposed_by}**\n "
                     f"- without any joined player\n ")
        st.write("")
        submitted = st.form_submit_button("⛔ Yes, delete table and its joined player(s)")
        if submitted:
            stu.delete_callback(table_id)
            st.rerun()


def display_table_proposition(section_name, compact, table_id, game_name, bgg_game_id, proposed_by, max_players, date, time, duration, notes, joined_count, joined_players):
    # Check if the BGG game ID is valid and set the BGG URL
    if bgg_game_id and int(bgg_game_id) >= 1:
        bgg_url = get_bgg_url(bgg_game_id)
        st.subheader(f"Table {table_id}: [{game_name}]({bgg_url})", anchor=f"table-{table_id}")
    else:
        st.subheader(f"Table {table_id}: {game_name}", anchor=f"table-{table_id}")

    # Create three columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if bgg_game_id and int(bgg_game_id) >= 1:
            image_url, game_description, categories, mechanics = get_bgg_game_info(bgg_game_id)
            image_width = 300 if not compact else 150
            caption = f"{game_description[:120]}..." if not compact else None
            if not image_url:
                image_url = stu.DEFAULT_IMAGE_URL
            st.image(image_url, width=image_width, caption=caption)
            if not compact:
                stu.st_write(f"<b>Categories:</b> {', '.join(categories)}")
                stu.st_write(f"<b>Mechanics:</b> {', '.join(mechanics)}")
        else:
            st.image(stu.DEFAULT_IMAGE_URL)

    with col2:
        if not compact:
            st.write(f"**Proposed By:**&nbsp;{proposed_by}")
            st.write(f"**Max Players:**&nbsp;&nbsp;{max_players}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time.strftime('%H:%M')}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")
            st.write(f"**Notes:**")
            st.write(notes)
        else:
            st.write(f"**Proposed By:**&nbsp;{proposed_by}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")

    with col3:
        is_full = joined_count >= max_players
        st.write(f":{'red' if is_full else 'green'}[**Joined Players ({joined_count}/{max_players}):**]")
        for joined_player in joined_players or []:
            if joined_player is not None:
                player_col1, player_col2 = st.columns([1, 1])
                with player_col1:
                    st.write(f"- {joined_player}")
                with player_col2:
                    # LEAVE
                    st.button(
                        "⛔ Leave",
                        key=f"leave_{table_id}_{joined_player}_{section_name}",
                        on_click=stu.leave_callback, args=[table_id, joined_player],
                        disabled=not stu.can_current_user_leave(joined_player, proposed_by),
                        help="Only the table owner or the player himself can leave a table."
                    )

    # Create four columns for action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if not is_full:
            if st.session_state['username']:
                st.button(
                    # JOIN
                    f"✅ Join Table {table_id}" if not stu.username_in_joined_players(joined_players) else "✅ *Already joined*",
                    key=f"join_{table_id}_{section_name}",
                    use_container_width=True,
                    disabled=stu.username_in_joined_players(joined_players),
                    on_click=stu.join_callback, args=[table_id, st.session_state['username']]
                )
            else:
                st.warning("Set a username to join a table.")
        else:
            st.warning(f"Table {table_id} is full.", )

    with col2:
        # DELETE
        if st.button(
            "⛔ Delete proposition",
            key=f"delete_{table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(proposed_by),
            help="Only the table owner can delete their tables."
        ):
            dialog_delete_table_proposition(table_id, game_name, joined_count, joined_players, proposed_by)
    with col3:
        if st.button(
            "🖋️ Edit",
            key=f"edit_{table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(proposed_by),
            help="Only the table owner can edit their tables."
        ):
            dialog_edit_table_proposition(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, joined_count)

    with col4:
        pass


def create_table_proposition():
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

    if bgg_game_id:
        st.write(f"Selected BGG Game ID: {bgg_game_id}")
    with st.form(key="create_new_proposition_form", border=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.number_input("Max Number of Players", min_value=1, max_value=100, step=1, key="max_players")
        with col2:
            st.number_input("Duration (in hours)", min_value=1, max_value=24, step=1, key="duration")
        col1, col2 = st.columns([1, 1])
        with col1:
            default_date_str = os.environ.get('DEFAULT_DATE')
            default_date = datetime.strptime(default_date_str, '%Y-%m-%d') if default_date_str else datetime.now()
            date_time = st.date_input("Date", value=default_date, key="date")
        with col2:
            # OLD version with granular time selection:
            # time = st.time_input("Time", step=60*30, key="time")
            # NEW version with Morning, Afternoon, Evening and Night
            time_options = ["09:00 - Morning", "14:00 - Afternoon", "18:00 - Evening", "22:00 - Night"]
            time_option = st.selectbox("Time Slot", options=time_options, key="time_option", help="Choose a time slot, you can change it in a more granular way once created, using '🖋️Edit'")
            time = stu.time_option_to_time(time_option)

        st.text_area("Notes", key="notes")

        st.checkbox("Join me by default to this table once created", key="join_me_by_default", value=True)
        stu.st_write("By default, you'll be added to this table once created. To avoid this, disable the above option")

        if st.session_state['username']:
            if st.form_submit_button("Create Proposition", on_click=stu.create_callback, args=[selected_game[1] if selected_game else None, bgg_game_id]):
                st.success(f"Table proposition created successfully: {selected_game[1]} - {date_time} {time.strftime('%H:%M')}")
                if st.session_state.join_me_by_default:
                    st.success(f"You have also joined this table by default as {st.session_state.username}.")

        else:
            st.form_submit_button("Create Proposition", disabled=True)
            st.warning("Set a username to create a proposition.")


def view_table_propositions(compact=False):
    for proposition in st.session_state.propositions:
        (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by,
         joined_count, joined_players) = proposition
        display_table_proposition(
            section_name="list",
            compact=compact,
            table_id=table_id,
            game_name=game_name,
            bgg_game_id=bgg_game_id,
            proposed_by=proposed_by,
            max_players=max_players,
            date=date,
            time=time,
            duration=duration,
            notes=notes,
            joined_count=joined_count,
            joined_players=joined_players
        )


def timeline_table_propositions(compact=False):
    df = stu.table_propositions_to_df(add_group=True, add_status=True, add_start_and_end_date=True)

    chart = timeline_chart(df)
    selected_data = st.altair_chart(chart, use_container_width=True, on_select="rerun", theme=None)

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("param_1", {}) and len(selected_data["selection"]["param_1"]) != 0:
            _id = selected_data["selection"]["param_1"][0]['table_id']
            selected_row = df[df['table_id'] == _id].iloc[0]
            display_table_proposition(
                section_name="timeline",
                compact=compact,
                table_id=int(selected_row['table_id']),
                game_name=selected_row['game_name'],
                bgg_game_id=selected_row['bgg_game_id'],
                proposed_by=selected_row['proposed_by'],
                max_players=selected_row['max_players'],
                date=selected_row['start_datetime'].date(),
                time=selected_row['start_datetime'].time(),
                duration=selected_row['duration'],
                notes=selected_row['notes'],
                joined_count=selected_row['joined_count'],
                joined_players=selected_row['joined_players']
            )

def dataframe_table_propositions(compact=False):

    default_columns = ['image', 'time', 'game_name', 'duration', 'players', 'proposed_by', 'joined', 'bgg']
    all_columns = ['table_id', 'image', 'time', 'game_name', 'duration', 'date', 'players', 'joined_players', 'proposed_by', 'joined', 'bgg']
    st.multiselect("Columns", options=all_columns, default=default_columns, key="columns_order")

    df = stu.table_propositions_to_df(add_image_url=True, add_bgg_url=True, add_players_fraction=True, add_joined=True)

    column_config = {
        "table_id":  st.column_config.TextColumn("ID", width="small"),
        "image": st.column_config.ImageColumn("Image", width="small"),
        "bgg":  st.column_config.LinkColumn("BGG", display_text="link"),
        "date":  st.column_config.DateColumn("Date"),
        "time": st.column_config.TimeColumn("Time", format='HH:mm'),
        "duration": st.column_config.NumberColumn("Duration", format="%dh", width="small"),
        "players": st.column_config.TextColumn("Players"),
        "joined_players": st.column_config.ListColumn("Joined Players"),
        "game_name": st.column_config.TextColumn("Name"),
        "proposed_by": st.column_config.TextColumn("Proposed By"),
        "joined": st.column_config.CheckboxColumn("Joined", width="small")
    }

    selected_data = st.dataframe(df, hide_index=True, use_container_width=True, column_config=column_config, column_order=st.session_state.columns_order, on_select="rerun", selection_mode="single-row")

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("rows", {}) and len(selected_data["selection"]["rows"]) != 0:
            _id = selected_data["selection"]["rows"][0]
            selected_row = df.iloc[_id]
            display_table_proposition(
                section_name="timeline",
                compact=compact,
                table_id=int(selected_row['table_id']),
                game_name=selected_row['game_name'],
                bgg_game_id=selected_row['bgg_game_id'],
                proposed_by=selected_row['proposed_by'],
                max_players=selected_row['max_players'],
                date=selected_row['date'],
                time=selected_row['time'],
                duration=selected_row['duration'],
                notes=selected_row['notes'],
                joined_count=selected_row['joined_count'],
                joined_players=selected_row['joined_players']
            )


st.title(f"{stu.get_title()}")

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
        st.info(f"Welcome back, **{st.session_state['username']}**\n\n*Use the User tab to edit your username*")
    else:
        st.warning("Set a username to join tables.\n\nUse the User tab to edit your username")
    with st.container(border=True):
        st.selectbox("View mode", options=["📜List", "📊Timeline", "◻️Table"], key="view_mode")
        st.toggle("Compact view", key="compact_view")
    with st.expander("🔒 God Mode"):
        god_mode_is_active = st.toggle("God Mode", key="god_mode", value=False, disabled=not st.session_state.user.is_admin)
        if st.session_state.user.is_admin:
            if god_mode_is_active:
                st.warning("God Mode is **active**. You can do anything you want. Be careful!")
            else:
                st.info("God Mode is **disabled**. You can only act as a normal user now")

tab1, tab2, tab3, tab4 = st.tabs(["📜View/Join", "➕Create", "🗺️Map", "🧑🏻User"])
with tab1:
    view_start_time = time_time()

    refresh_col, filter_col, fake_col = st.columns([1, 1, 4])
    with refresh_col:
        refresh_button = st.button("🔄️ Refresh", key="refresh", use_container_width=True)
        if refresh_button:
            stu.refresh_table_propositions("Refresh")
    with filter_col:
        filter_label_num_active_filters = stu.get_num_active_filters(as_str=True)
        with st.popover(f"🔍 {filter_label_num_active_filters}Filters:", use_container_width=True):
            st.toggle("Joined by me", key="joined_by_me", value=False, on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering"}, disabled=not st.session_state['username'])
    with fake_col:
        pass

    if len(st.session_state.propositions) == 0:
        st.info("No table propositions available, use the \"**➕Create**\" tab to create a new one."
                "\n\n*NB: tables are automatically hidden after 1 day*")
    else:
        if st.session_state['view_mode'] == "📜List":
            view_table_propositions(st.session_state['compact_view'])
        elif st.session_state['view_mode'] == "📊Timeline":
            timeline_table_propositions(st.session_state['compact_view'])
        else:
            dataframe_table_propositions(st.session_state['compact_view'])

    print(f"Table propositions VIEW refreshed in {(time_time() - view_start_time):2f}s")
with tab2:
    create_table_proposition()
with tab3:
    gmap_url = os.environ.get('GMAP_MAP_URL')
    if gmap_url:
        st.components.v1.iframe(gmap_url, height=500)
    else:
        st.warning("GMAP_MAP_URL environment variable not set")
with tab4:
    st.subheader("User settings")

    col1, col2 = st.columns([1, 4])
    col1.text_input("User ID", value=st.session_state.user.user_id, disabled=True)
    col2.text_input("Email", value=st.session_state.user.email, disabled=True)
    with st.form("user_setting_form", border=False):
        st.text_input("Username", value=st.session_state.username, key="username_user_setting", disabled=False)
        col_name, col_surname =  st.columns([1, 1])
        col_name.text_input("Name", value=st.session_state.user.name, key="name_user_setting", disabled=False)
        col_surname.text_input("Surname",  value=st.session_state.user.surname, key="surname_user_setting", disabled=False)
        col_bgg_username, col_telegram_username =  st.columns([1, 1])
        col_bgg_username.text_input("BGG username",  value=st.session_state.user.bgg_username, key="bgg_username_user_setting", disabled=False)
        with col_bgg_username:
            if st.session_state.user.bgg_username:
                stu.st_write(get_bgg_profile_page_url(st.session_state.user.bgg_username, as_html_link=True))
            else:
                stu.st_write("No BGG username set, set it to test the link")
        col_telegram_username.text_input("Telegram username (without the '@')", value=st.session_state.user.telegram_username, key="telegram_username_user_setting", disabled=False)
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
            else:
                st.error(f"Error updating username: {st.session_state.update_username_from_user_error}")
            st.session_state["update_username_from_user_error"] = None
    st.toggle("Admin", value=st.session_state.user.is_admin, disabled=True, help="Ask the admin to change this setting for your user")

    st.subheader("User locations")
    stu.manage_user_locations(user_id=st.session_state.user.user_id)

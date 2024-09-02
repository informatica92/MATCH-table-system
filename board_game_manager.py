import streamlit as st

from time import sleep, time as time_time
from datetime import datetime, timedelta
import os

from streamlit_timeline import st_timeline

from utils.telegram_notifications import TelegramNotifications
from utils.sql_manager import SQLManager
from utils.bgg_manager import search_bgg_games, get_bgg_game_info, get_bgg_url

st.set_page_config(page_title="Board Game Proposals", layout="wide")

DEFAULT_IMAGE_URL = "images/no_image.jpg"

BGG_GAME_ID_HELP = ("It's the id in the BGG URL. EX: for Wingspan the URL is "
                    "https://boardgamegeek.com/boardgame/266192/wingspan, hence the BGG game id is 266192")

CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;'>{label}</p>"

sql_manager = SQLManager()
sql_manager.create_tables()

telegram_bot = TelegramNotifications()


def st_write(label, size=12):
    st.write(CUSTOM_TEXT_WITH_LABEL_AND_SIZE.format(label=label, size=size), unsafe_allow_html=True)


def refresh_table_propositions():
    query_start_time = time_time()
    st.session_state.propositions = sql_manager.get_table_propositions()
    print(f"Table propositions QUERY refreshed in {(time_time() - query_start_time):2f}s "
          f"({len(st.session_state.propositions)} rows)")


def display_table_proposition(section_name, compact, table_id, game_name, bgg_game_id, proposed_by, max_players, date, time, duration, notes, joined_count, joined_players):
    # Check if the BGG game ID is valid and set the BGG URL
    if bgg_game_id and int(bgg_game_id) > 1:
        bgg_url = get_bgg_url(bgg_game_id)
        st.subheader(f"Table {table_id}: [{game_name}]({bgg_url})", anchor=f"table-{table_id}")
    else:
        st.subheader(f"Table {table_id}: {game_name}", anchor=f"table-{table_id}")

    # Create three columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if bgg_game_id and int(bgg_game_id) > 1:
            image_url, game_description, categories, mechanics = get_bgg_game_info(bgg_game_id)
            image_width = 300 if not compact else 150
            caption = f"{game_description[:120]}..." if not compact else None
            if not image_url:
                image_url = DEFAULT_IMAGE_URL
            st.image(image_url, width=image_width, caption=caption)
            if not compact:
                st_write(f"<b>Categories:</b> {', '.join(categories)}")
                st_write(f"<b>Mechanics:</b> {', '.join(mechanics)}")
        else:
            st.image(DEFAULT_IMAGE_URL)

    with col2:
        if not compact:
            st.write(f"**Proposed By:**&nbsp;{proposed_by}")
            st.write(f"**Max Players:**&nbsp;&nbsp;{max_players}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time}")
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
                    leave_table = st.button("⛔Leave", key=f"leave_{table_id}_{joined_player}_{section_name}")
                    if leave_table:
                        sql_manager.leave_table(table_id, joined_player)
                        st.success(f"{joined_player} left Table {table_id}.")
                        sleep(1)
                        refresh_table_propositions()
                        st.rerun()

    # Create four columns for action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if not is_full:
            if st.session_state['username']:
                if st.button(
                        f"✅Join Table {table_id}" if st.session_state['username'] not in joined_players else "✅*Already joined*",
                        key=f"join_{table_id}_{section_name}",
                        use_container_width=True,
                        disabled=st.session_state['username'] in joined_players
                ):
                    try:
                        sql_manager.join_table(table_id, st.session_state['username'])
                        st.success(
                            f"You have successfully joined Table {table_id} as {st.session_state['username']}!"
                        )
                        sleep(1)
                        refresh_table_propositions()
                        st.rerun()
                    except AttributeError:
                        st.warning("You have already joined this table.")
            else:
                st.warning("Set a username to join a table.")
        else:
            st.warning(f"Table {table_id} is full.")

    with col2:
        if st.button(
                "⛔Delete proposition" if not joined_count else "⛔*Can't delete non empty tables*",
                key=f"delete_{table_id}_{section_name}",
                use_container_width=True,
                disabled=joined_count
        ):
            sql_manager.delete_proposition(table_id)
            st.success(f"You have successfully deleted Table {table_id}")
            sleep(1)
            refresh_table_propositions()
            st.rerun()

    with col3:
        pass

    with col4:
        pass


def create_table_proposition():
    st.header("➕Create a New Table Proposition")

    game_name = st.text_input("Search for Game Name")
    st_write("Write a game name in the above text box and press ENTER. The matching games from BGG will appear here:")
    bgg_game_id = None

    try:
        matching_games = search_bgg_games(game_name)
    except AttributeError as e:
        st.error(f"Error searching for games: {e}")
        matching_games = []

    selected_game = st.selectbox("Select the matching game", matching_games, format_func=lambda x: x[1])
    st_write("Select the matching game from BGG for auto detecting information like the board game image")
    if selected_game:
        bgg_game_id = selected_game[0]

    if bgg_game_id:
        st.write(f"Selected BGG Game ID: {bgg_game_id}")
    with st.form(key="create_new_proposition_form", border=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            max_players = st.number_input("Max Number of Players", min_value=1, max_value=100, step=1)
        with col2:
            duration = st.number_input("Duration (in hours)", min_value=1, max_value=24, step=1)
        col1, col2 = st.columns([1, 1])
        with col1:
            default_date_str = os.environ.get('DEFAULT_DATE')
            default_date = datetime.strptime(default_date_str, '%Y-%m-%d') if default_date_str else datetime.now()
            date_time = st.date_input("Date", value=default_date)
        with col2:
            time = st.time_input("Time", step=60*30)
        notes = st.text_area("Notes")

        if st.session_state['username']:
            if st.form_submit_button("Create Proposition"):
                sql_manager.create_proposition(
                    selected_game[1],
                    max_players,
                    date_time,
                    time,
                    duration,
                    notes,
                    bgg_game_id,
                    st.session_state.username
                )
                st.success("Table proposition created successfully!")

                telegram_bot.send_new_table_message(
                    selected_game[1],
                    max_players,
                    date_time.strftime('%Y-%m-%d'),
                    time.strftime('%H:%M:%S'),
                    duration,
                    st.session_state.username
                )
                sleep(1)
                refresh_table_propositions()
                st.rerun()
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
    items = []
    groups = [
        {"id": 0, "content": "Morning (09:00 - 12:00)", "style": "background: #f7eda6"},
        {"id": 1, "content": "Afternoon (12:00pm - 18:00)", "style": "background: #a6f7ee"},  # light blue
        {"id": 2, "content": "Evening (18:00 - 00:00)", "style": "background: #a6adf7"}
    ]
    for proposition in st.session_state.propositions:
        (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by,
         joined_count, joined_players) = proposition

        start_datetime_str = f"{date} {time}"
        end_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M:%S') + timedelta(hours=duration)
        end_datetime_str = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # create a "group" variable that is "morning", "afternoon" or "evening" based on the time of day
        group = 0 if time.hour < 12 else "1" if time.hour < 18 else "2"

        items.append(
            {
                "id": table_id,
                "content": game_name,
                "start": start_datetime_str,
                "date": str(date),
                "time": str(time),
                "end": end_datetime_str,
                "max_players": max_players,
                "joined_count": joined_count,
                "joined_players": joined_players,
                "proposed_by": proposed_by,
                "group": group,
                "bgg_game_id": bgg_game_id,
                "duration": duration,
                "notes": notes,
                "style": "background: #FF5733" if joined_count == max_players else "background: #DAF7A6"
            }
        )
    timeline = st_timeline(items, groups=groups, options={}, height="300px")
    st.subheader("Selected item")
    if timeline:
        display_table_proposition(
            section_name="timeline",
            compact=compact,
            table_id=timeline['id'],
            game_name=timeline['content'],
            bgg_game_id=timeline['bgg_game_id'],
            proposed_by=timeline['proposed_by'],
            max_players=timeline['max_players'],
            date=timeline['date'],
            time=timeline['time'],
            duration=timeline['duration'],
            notes=timeline['notes'],
            joined_count=timeline['joined_count'],
            joined_players=timeline['joined_players']
        )


st.title("🎴 Board Game Reservation Manager")

# Initialize username in session state
if 'username' not in st.session_state:
    st.session_state['username'] = None

if "propositions" not in st.session_state:
    print("Initializing st.session_state.propositions")
    refresh_table_propositions()

# Add a username setting in the sidebar
with st.sidebar:
    st.image("images/logo.jpg")
    st.header("Set Your Username")

    username = st.text_input("Username", value=st.session_state['username'])

    if username:
        username = username.strip()
        st.session_state['username'] = username
        st.success(f"Username set to: {username}")
    else:
        st.session_state['username'] = None
        st.warning("Please set a username to join a table.")

    st.toggle("Compact view", key="compact_view")
    st.selectbox("View mode", options=["📜List", "📊Timeline"], key="view_mode")

tab1, tab2 = st.tabs(["📜View and Join Table Propositions", "➕Create Table Proposition"])
with tab1:
    view_start_time = time_time()

    refresh_button = st.button("🔄️Refresh", key="refresh")
    if refresh_button:
        refresh_table_propositions()

    if len(st.session_state.propositions) == 0:
        st.info("No table propositions available.")
    else:
        if st.session_state['view_mode'] == "📜List":
            view_table_propositions(st.session_state['compact_view'])
        else:
            timeline_table_propositions(st.session_state['compact_view'])

    print(f"Table propositions VIEW refreshed in {(time_time() - view_start_time):2f}s")
with tab2:
    create_table_proposition()

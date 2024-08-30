import streamlit as st
import psycopg2
import requests
import xml.etree.ElementTree as et
from time import sleep
from datetime import datetime
import os

from utils.telegram_notifications import TelegramNotifications
from utils.sql_manager import SQLManager

st.set_page_config(page_title="Board Game Proposals", layout="wide")

DEFAULT_IMAGE_URL = "images/no_image.jpg"

BGG_GAME_ID_HELP = ("It's the id in the BGG URL. EX: for Wingspan the URL is "
                    "https://boardgamegeek.com/boardgame/266192/wingspan, hence the BGG game id is 266192")

CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;'>{label}</p>"

sql_manager = SQLManager()
sql_manager.create_tables()

telegram_bot = TelegramNotifications()


def get_bgg_game_info(game_id):
    # BGG API URL for game details
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"

    try:
        # Make a GET request to fetch the game data
        response = requests.get(url)

        # Raise an HTTPError for bad responses
        response.raise_for_status()

        # Parse the XML response
        root = et.fromstring(response.content)

        # Find the image tag and extract the URL
        image_url = root.find('item/image').text

        game_description = root.find('item/description').text

        categories = []
        for category in root.findall('item/link[@type="boardgamecategory"]'):
            categories.append(category.get('value'))

        mechanics = []
        for mechanic in root.findall('item/link[@type="boardgamemechanic"]'):
            mechanics.append(mechanic.get('value'))

        return image_url, game_description, categories, mechanics
    except Exception as e:
        print(f"Error fetching game image: {e}")
        return None


def get_bgg_url(game_id):
    return f"https://boardgamegeek.com/boardgame/{game_id}"


def search_bgg_games(game_name):
    url = f"https://boardgamegeek.com/xmlapi2/search?query={game_name}&type=boardgame"
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = et.fromstring(response.content)

        games = []
        for item in root.findall('item'):
            game_id = item.get('id')
            name = item.find('name').get('value')
            year = item.find('yearpublished')
            year = year.get('value') if year is not None else "Unknown Year"
            games.append((game_id, f"{name} ({year})"))

        return games
    except Exception as e:
        st.error(f"Error searching for games: {e}")
        return []


def st_write(label, size=12):
    st.write(CUSTOM_TEXT_WITH_LABEL_AND_SIZE.format(label=label, size=size), unsafe_allow_html=True)


def refresh_table_propositions():
    st.session_state.propositions = sql_manager.get_table_propositions()


def create_table_proposition():
    st.header("➕Create a New Table Proposition")

    game_name = st.text_input("Search for Game Name")
    st_write("Write a game name in the above text box and press ENTER. The matching games from BGG will appear here:")
    bgg_game_id = None

    matching_games = search_bgg_games(game_name)

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
            if st.form_submit_button("Create Proposition", on_click=refresh_table_propositions()):
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
                st.rerun()
        else:
            st.form_submit_button("Create Proposition", disabled=True)
            st.warning("Set a username to create a proposition.")


def view_table_propositions(compact=False):
    refresh_button = st.button("🔄️Refresh")
    if refresh_button:
        refresh_table_propositions()

    if len(st.session_state.propositions) == 0:
        st.info("No table propositions available.")
    else:
        for proposition in st.session_state.propositions:
            (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by,
             joined_count, joined_players) = proposition
            if bgg_game_id and int(bgg_game_id) > 1:
                bgg_url = get_bgg_url(bgg_game_id)
                st.subheader(f"Table {table_id}: [{game_name}]({bgg_url})")
            else:
                st.subheader(f"Table {table_id}: {game_name}")
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
                        st_write(label=f"<b>Categories:</b> {', '.join(categories)}")
                        st_write(label=f"<b>Mechanics:</b> {', '.join(mechanics)}")
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
                if compact:
                    st.write(f"**Proposed By:**&nbsp;{proposed_by}")
                    st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time}")
                    st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")
            with col3:
                st.write(f"**Joined Players ({joined_count}/{max_players}):**")
                for joined_player in joined_players:
                    if joined_player is not None:
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.write(f"- {joined_player}")
                        with col2:
                            leave_table = st.button("⛔Leave", key=f"leave_{table_id}_{joined_player}")
                            if leave_table:
                                sql_manager.leave_table(table_id, joined_player)
                                st.success(f"{joined_player} left Table {table_id}.")
                                sleep(1)
                                st.rerun()

            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if joined_count < max_players:
                    if st.session_state['username']:
                        if st.button(
                                f"✅Join Table {table_id}" if username not in joined_players else "✅*Already joined*",
                                key=f"join_{table_id}",
                                use_container_width=True,
                                disabled=username in joined_players
                        ):
                            try:
                                sql_manager.join_table(table_id, st.session_state.username)
                                st.success(
                                    f"You have successfully joined Table {table_id} as {st.session_state.username}!"
                                )
                                sleep(1)
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
                        key=f"delete_{table_id}",
                        use_container_width=True,
                        disabled=joined_count
                ):
                    sql_manager.delete_proposition(table_id)
                    st.success(f"You have successfully deleted Table {table_id}")
                    sleep(1)
                    st.rerun()
            with col3:
                pass
            with col4:
                pass


st.title("🎴 Board Game Reservation Manager")

# Initialize username in session state
if 'username' not in st.session_state:
    st.session_state['username'] = None

refresh_table_propositions()

# Add a username setting in the sidebar
with st.sidebar:
    st.image("images/logo.jpg")
    st.header("Set Your Username")

    username = st.text_input("Username", value=st.session_state['username'])

    if username:
        st.session_state['username'] = username
        st.success(f"Username set to: {username}")
    else:
        st.session_state['username'] = None
        st.warning("Please set a username to join a table.")

    st.toggle("Compact view", key="compact_view")

    # st.text("""
    # TODO:
    #  - add filters
    #     - add "only mines"
    # """)

tab1, tab2 = st.tabs(["📜View and Join Table Propositions", "➕Create Table Proposition"])
with tab1:
    view_table_propositions(st.session_state['compact_view'])
with tab2:
    create_table_proposition()

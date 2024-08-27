import streamlit as st
import psycopg2
import requests
import xml.etree.ElementTree as et
from time import sleep
import os

# Get PostgreSQL credentials from environment variables
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT', '5432')


def get_db_connection():
    # Initialize the PostgreSQL connection
    return psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )


def create_tables():
    # Create table propositions table if it doesn't exist
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS table_propositions (
                    id SERIAL PRIMARY KEY,
                    game_name TEXT,
                    max_players INTEGER,
                    date DATE,
                    time TIME,
                    duration INTEGER,
                    notes TEXT,
                    bgg_game_id INTEGER, 
                    proposed_by TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS joined_players (
                    id SERIAL PRIMARY KEY,
                    table_id INTEGER REFERENCES table_propositions(id) ON DELETE CASCADE,
                    player_name TEXT,
                    UNIQUE(table_id, player_name)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    username TEXT,
                    is_admin BOOLEAN DEFAULT FALSE)
                ''')
    conn.commit()
    c.close()
    conn.close()


create_tables()

DEFAULT_IMAGE_URL = "images/no_image.jpg"

BGG_GAME_ID_HELP = ("It's the id in the BGG URL. EX: for Wingspan the URL is "
                    "https://boardgamegeek.com/boardgame/266192/wingspan, hence the BGG game id is 266192")

CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;'>{label}</p>"

st.set_page_config(page_title="Board Game Proposals", layout="wide")


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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        '''
            SELECT
                tp.id,
                tp.game_name,
                tp.max_players,
                tp.date, tp.time,
                tp.duration,
                tp.notes,
                tp.bgg_game_id,
                tp.proposed_by,
                (SELECT COUNT(*) FROM joined_players jp WHERE jp.table_id = tp.id) as joined_count
            FROM table_propositions tp
        '''
    )
    st.session_state.propositions = c.fetchall()
    c.close()
    conn.close()


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

    col1, col2 = st.columns([1, 1])
    with col1:
        max_players = st.number_input("Max Number of Players", min_value=1, step=1)
    with col2:
        duration = st.number_input("Duration (in hours)", min_value=1, step=1)
    col1, col2 = st.columns([1, 1])
    with col1:
        date_time = st.date_input("Date")
    with col2:
        time = st.time_input("Time")
    notes = st.text_area("Notes")

    if st.session_state['username']:
        if st.button("Create Proposition", on_click=refresh_table_propositions()):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO table_propositions (
                    game_name, 
                    max_players, 
                    date, 
                    time, 
                    duration, 
                    notes, 
                    bgg_game_id, 
                    proposed_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                    selected_game[1],
                    max_players,
                    date_time.strftime('%Y-%m-%d'),
                    time.strftime('%H:%M:%S'),
                    duration,
                    notes,
                    bgg_game_id,
                    st.session_state.username
                )
            )
            conn.commit()
            c.close()
            conn.close()

            st.success("Table proposition created successfully!")
            sleep(1)
            st.rerun()
    else:
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
             joined_count) = proposition
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
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''SELECT player_name FROM joined_players WHERE table_id = %s''', (table_id,))
                joined_players = [row[0] for row in c.fetchall()]
                c.close()
                conn.close()
                for joined_player in joined_players:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"- {joined_player}")
                    with col2:
                        leave_table = st.button("⛔Leave", key=f"leave_{table_id}_{joined_player}")
                        if leave_table:
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute(
                                '''DELETE FROM joined_players WHERE table_id = %s AND player_name = %s''',
                                (table_id, joined_player)
                            )
                            conn.commit()
                            c.close()
                            conn.close()
                            st.success(f"{st.session_state.username} left Table {table_id}.")
                            sleep(1)
                            st.rerun()

            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if joined_count < max_players:
                    if st.session_state['username']:
                        if st.button(f"✅Join Table {table_id}", key=f"join_{table_id}", use_container_width=True):
                            conn = get_db_connection()
                            c = conn.cursor()
                            try:
                                c.execute(
                                    '''INSERT INTO joined_players (table_id, player_name) VALUES (%s, %s)''',
                                    (table_id, st.session_state['username'])
                                )
                                conn.commit()
                                st.success(
                                    f"You have successfully joined Table {table_id} as {st.session_state.username}!"
                                )
                                sleep(1)
                                st.rerun()
                            except psycopg2.IntegrityError:
                                st.warning("You have already joined this table.")
                            finally:
                                c.close()
                                conn.close()
                    else:
                        st.warning("Set a username to join a table.")
                else:
                    st.warning(f"Table {table_id} is full.")
            with col2:
                if st.button("⛔Delete proposition", key=f"delete_{table_id}", use_container_width=True):
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute(
                        '''DELETE FROM table_propositions WHERE id = %s''',
                        (table_id, )
                    )
                    conn.commit()
                    c.close()
                    conn.close()
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
    # st.info(st.experimental_user.email)  # test@example.com if local, otherwise Streamlit Cloud email
    username = st.text_input("Username")

    if username:
        st.session_state['username'] = username
        st.success(f"Username set to: {username}")
    else:
        st.session_state['username'] = None
        st.warning("Please set a username to join a table.")

    st.toggle("Compact view", key="compact_view")

    st.text("""
    TODO: 
     - add filters
        - add "only mines"
     - cache the username somehow
     - download/restore db in case of database reset 
    """)

tab1, tab2 = st.tabs(["📜View and Join Table Propositions", "➕Create Table Proposition"])
with tab1:
    view_table_propositions(st.session_state['compact_view'])
with tab2:
    create_table_proposition()

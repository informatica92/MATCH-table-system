import streamlit as st
import sqlite3
import requests
import xml.etree.ElementTree as et
from time import sleep

# Initialize SQLite database connection
conn = sqlite3.connect('board_game_manager.db')
c = conn.cursor()

# Create table propositions table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS table_propositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT,
                max_players INTEGER,
                date TEXT,
                time TEXT,
                duration INTEGER,
                notes TEXT,
                bgg_game_id INTEGER, 
                proposed_by TEXT
            )''')

# Create joined players table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS joined_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER,
                player_name TEXT,
                FOREIGN KEY (table_id) REFERENCES table_propositions (id),
                UNIQUE(table_id, player_name)
            )''')

conn.commit()

DEFAULT_IMAGE_URL = ("https://cf.geekdo-images.com/zxVVmggfpHJpmnJY9j-k1w__imagepage/img/6AJ0hDAeJlICZkzaeIhZA_fSiAI="
                     "/fit-in/900x600/filters:no_upscale():strip_icc()/pic1657689.jpg")


st.set_page_config(page_title="Board Game Proposals", layout="wide")


def get_bgg_game_image(game_id):
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

        return image_url
    except Exception as e:
        print(f"Error fetching game image: {e}")
        return None


def refresh_table_propositions():
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


def create_table_proposition():
    st.header("➕Create a New Table Proposition")

    game_name = st.text_input("Game Name")
    bgg_game_id = st.number_input("BGG Game ID", format="%.0f")
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                    game_name,
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

            st.success("Table proposition created successfully!")
            sleep(1)
            st.rerun()
    else:
        st.warning("Set a username to create a proposition.")


def view_table_propositions():
    refresh_button = st.button("🔄️Refresh")
    if refresh_button:
        refresh_table_propositions()

    if len(st.session_state.propositions) == 0:
        st.info("No table propositions available.")
    else:
        for proposition in st.session_state.propositions:
            print("PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
            print(proposition)
            (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by,
             joined_count) = proposition
            st.subheader(f"Table {table_id}: {game_name}")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if bgg_game_id and int(bgg_game_id) > 1:
                    st.image(get_bgg_game_image(bgg_game_id), width=300)
                else:
                    st.image(DEFAULT_IMAGE_URL)
            with col2:
                st.write(f"**Proposed By:**&nbsp;{proposed_by}")
                st.write(f"**Max Players:**&nbsp;&nbsp;{max_players}")
                st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time}")
                st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")
                st.write(f"**Notes:**")
                st.write(notes)
            with col3:
                st.write(f"**Joined Players ({joined_count}/{max_players}):**")
                # Display joined players
                c.execute('''SELECT player_name FROM joined_players WHERE table_id = ?''', (table_id,))
                joined_players = [row[0] for row in c.fetchall()]
                # st.write(", ".join(joined_players) if joined_players else "None")
                for joined_player in joined_players:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"- {joined_player}")
                    with col2:
                        leave_table = st.button("⛔Leave", key=f"leave_{table_id}_{joined_player}")
                        if leave_table:
                            c.execute(
                                '''DELETE FROM joined_players WHERE table_id = ? AND player_name = ?''',
                                (table_id, joined_player)
                            )
                            conn.commit()
                            st.success(f"{st.session_state.username} left Table {table_id}.")
                            sleep(1)
                            st.rerun()

            col1, col2 = st.columns([1, 1])
            with col1:
                if joined_count < max_players:
                    if st.session_state['username']:
                        if st.button(f"✅Join Table {table_id}", key=f"join_{table_id}"):
                            # Insert into joined players
                            try:
                                c.execute(
                                    '''INSERT INTO joined_players (table_id, player_name) VALUES (?, ?)''',
                                    (table_id, st.session_state['username'])
                                )
                                conn.commit()
                                st.success(
                                    f"You have successfully joined Table {table_id} as {st.session_state.username}!"
                                )
                                sleep(1)
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.warning("You have already joined this table.")
                    else:
                        st.warning("Set a username to join a table.")
                else:
                    st.warning(f"Table {table_id} is full.")
            with col2:
                if st.button("⛔Delete proposition", key=f"delete_{table_id}"):
                    c.execute(
                        '''DELETE FROM table_propositions WHERE id = ?''',
                        (table_id, )
                    )
                    conn.commit()
                    st.success(f"You have successfully deleted Table {table_id}")
                    sleep(1)
                    st.rerun()


st.title("🎴 Board Game Reservation Manager")

# Initialize username in session state
if 'username' not in st.session_state:
    st.session_state['username'] = None

refresh_table_propositions()

# Add a username setting in the sidebar
st.sidebar.header("Set Your Username")
username = st.sidebar.text_input("Username")

if username:
    st.session_state['username'] = username
    st.sidebar.success(f"Username set to: {username}")
else:
    st.session_state['username'] = None
    st.sidebar.warning("Please set a username to join a table.")

st.sidebar.text("""
TODO: 
 - add filters
 - add logo
""")


tab1,  tab2 = st.tabs(["📜View and Join Table Propositions", "➕Create Table Proposition"])
with tab1:
    view_table_propositions()
with tab2:
    create_table_proposition()

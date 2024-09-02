import streamlit as st
import altair as alt
import pandas as pd

from time import sleep, time as time_time
from datetime import datetime, timedelta
import os

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
    joined_by_me = st.session_state.joined_by_me
    filter_username = st.session_state.username
    st.session_state.propositions = sql_manager.get_table_propositions(joined_by_me, filter_username)
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
                last_row_id = sql_manager.create_proposition(
                    selected_game[1],
                    max_players,
                    date_time,
                    time,
                    duration,
                    notes,
                    bgg_game_id,
                    st.session_state.username
                )
                st.success(f"Table proposition created successfully! (id: {last_row_id})")

                telegram_bot.send_new_table_message(
                    selected_game[1],
                    max_players,
                    date_time.strftime('%Y-%m-%d'),
                    time.strftime('%H:%M:%S'),
                    duration,
                    st.session_state.username,
                    last_row_id
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
    propositions = st.session_state.propositions
    data = []

    for proposition in propositions:
        (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by,
         joined_count, joined_players) = proposition

        start_datetime_str = f"{date} {time}"
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M:%S')
        end_datetime = start_datetime + timedelta(hours=duration)

        # Determine the group based on the time of day
        group = 'Morning' if start_datetime.hour < 12 else 'Afternoon' if start_datetime.hour < 18 else 'Evening'

        data.append({
            'table_id': table_id,
            'game_name': game_name,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'max_players': max_players,
            'joined_count': joined_count,
            'joined_players': joined_players,
            'proposed_by': proposed_by,
            'group': group,
            'bgg_game_id': bgg_game_id,
            'duration': duration,
            'notes': notes,
            'status': 'Full' if joined_count == max_players else 'Available'
        })

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create the Altair chart
    # # Handle user selection based on Altair interaction (using nearest or selection)
    selection = alt.selection_point(
        fields=['table_id'],
        # on='mouseover',
        # empty='none',
        # clear='mouseout'
    )
    chart = alt.Chart(df).mark_bar().encode(
        x='start_datetime:T',
        x2='end_datetime:T',
        y=alt.Y('game_name:N', title=None),
        color=alt.Color('status:N', scale=alt.Scale(domain=['Full', 'Available'], range=['#FF5733', '#DAF7A6'])),
        tooltip=['game_name:N', 'proposed_by:N', 'max_players:Q', 'joined_count:Q', 'duration:Q']
    ).properties(
        width='container',
        height=300
    ).interactive(

    ).add_params(
        selection
    ).encode(
        opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
    )

    selected_data = st.altair_chart(chart, use_container_width=True, on_select=lambda: print("timeline selection"))

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

    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
    with col1:
        refresh_button = st.button("🔄️Refresh", key="refresh", use_container_width=True)
        if refresh_button:
            refresh_table_propositions()
    with col2:
        st_write("🔍 Filters:", size=25)
    with col3:
        st.toggle("Joined by me", key="joined_by_me", value=False, on_change=refresh_table_propositions(), disabled=not st.session_state['username'])
    with col4:
        pass

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

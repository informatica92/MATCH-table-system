import streamlit as st

import pandas as pd
from time import time as time_time
from datetime import datetime, timedelta

from utils.telegram_notifications import TelegramNotifications
from utils.sql_manager import SQLManager
from utils.bgg_manager import get_bgg_game_info, get_bgg_url


DEFAULT_IMAGE_URL = "images/no_image.jpg"

BGG_GAME_ID_HELP = ("It's the id in the BGG URL. EX: for Wingspan the URL is "
                    "https://boardgamegeek.com/boardgame/266192/wingspan, hence the BGG game id is 266192")

CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;'>{label}</p>"

BOUNCE_SIDEBAR_ICON = r"""
    <style>
    .st-emotion-cache-1f3w014 {
            animation: bounce 2s ease infinite;
        }
    @keyframes bounce {
        70% { transform:translateY(0%); }
        80% { transform:translateY(-15%); }
        90% { transform:translateY(0%); }
        95% { transform:translateY(-7%); }
        97% { transform:translateY(0%); }
        99% { transform:translateY(-3%); }
        100% { transform:translateY(0); }
    }
    </style>
"""

sql_manager = SQLManager()
sql_manager.create_tables()

telegram_bot = TelegramNotifications()

def username_in_joined_players(joined_players: list[str]):
    if st.session_state.username:
        return st.session_state.username.lower() in [player.lower() for player in joined_players if player]
    else:
        return False


def st_write(label, size=12):
    st.write(CUSTOM_TEXT_WITH_LABEL_AND_SIZE.format(label=label, size=size), unsafe_allow_html=True)


def refresh_table_propositions(reason):
    query_start_time = time_time()
    if "joined_by_me" in st.session_state:
        joined_by_me = st.session_state.joined_by_me
    else:
        joined_by_me = False
    if joined_by_me and "username" in st.session_state:
        filter_username = st.session_state.username
    else:
        filter_username = None
    st.session_state.propositions = sql_manager.get_table_propositions(joined_by_me, filter_username)
    print(f"Table propositions QUERY [{reason}] refreshed in {(time_time() - query_start_time):2f}s "
          f"({len(st.session_state.propositions)} rows)")

def update_table_propositions(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id):
    sql_manager.update_table_proposition(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id)
    refresh_table_propositions("Table Update")

def table_propositions_to_df(
        add_start_and_end_date=False, add_group=False, add_status=False,
        add_image_url=False, add_bgg_url=False, add_players_fraction=False, add_joined=False,
):
    columns = ['table_id', 'game_name', 'max_players', 'date', 'time', 'duration', 'notes', 'bgg_game_id',
               'proposed_by', 'joined_count', 'joined_players']
    df = pd.DataFrame(st.session_state.propositions, columns=columns)

    if add_start_and_end_date:
        # concat date and time columns to get the start datetime
        df['start_datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
        # add 'duration' to 'start_datetime'
        df['end_datetime'] = df['start_datetime'] + pd.to_timedelta(df['duration'], unit='hour')

    if add_group:
        # 'Morning' if time.hour < 12 else 'Afternoon' if time.hour < 18 else 'Evening'
        df['group'] = df['time'].apply(lambda x: 'Morning' if x.hour < 12 else 'Afternoon' if x.hour < 18 else 'Evening')

    if add_status:
        df['status'] = df.apply(lambda x: 'Full' if x['joined_count'] == x['max_players'] else 'Available', axis=1)

    if add_image_url:
        df['image'] = df['bgg_game_id'].apply(lambda x: get_bgg_game_info(x)[0])  # image_url, description), categories, mechanics

    if add_bgg_url:
        df['bgg'] = df['bgg_game_id'].apply(get_bgg_url)

    if add_players_fraction:
        df['players'] = df['joined_count'].astype(str) + "/" + df['max_players'].astype(str)

    if add_joined:
        df['joined'] = df['joined_players'].apply(username_in_joined_players)

    return df.sort_values(["date", "time"])

# CAN THIS USER LEAVE / DELETE?

def can_current_user_leave(player_to_remove, proposed_by):
    if st.session_state.god_mode:
        return True  # god mode can leave anyone
    elif st.session_state.username and player_to_remove.lower() == st.session_state.username.lower():
        return True  # users can remove themselves
    elif st.session_state.username and proposed_by.lower() == st.session_state.username.lower():
        return True  # table owner can remove anyone at their tables
    else:
        return False

def can_current_user_delete(proposed_by):
    if st.session_state.god_mode:
        return True  # god mode can delete anything
    elif st.session_state.username and proposed_by.lower() == st.session_state.username.lower():
        return True  # table owner can remove their own tables
    else:
        return False

# CALLBACKS

def time_option_to_time(time_option):
    # time_option is a string with the following format "HH:MM - Morning|Afternoon|Evening|Night"
    time = datetime.strptime(time_option.split(" - ")[0], "%H:%M").time()
    return time

def join_callback(table_id, joining_username):
    try:
        sql_manager.join_table(table_id, joining_username)
        refresh_table_propositions("Join")
        st.toast(f"✅ Joined Table {table_id} as {joining_username}!")
    except AttributeError:
        st.toast("🚫 You have already joined this table.")


def leave_callback(table_id, leaving_username):
    sql_manager.leave_table(table_id, leaving_username)
    refresh_table_propositions("Leave")
    st.toast(f"⛔ {leaving_username} left Table {table_id}")

def delete_callback(table_id):
    sql_manager.delete_proposition(table_id)
    refresh_table_propositions("Delete")
    st.toast(f"⛔ Deleted Table {table_id}")

def create_callback(game_name, bgg_game_id):
    if game_name:
        last_row_id = sql_manager.create_proposition(
            game_name,
            st.session_state.max_players,
            st.session_state.date,
            time_option_to_time(st.session_state.time_option),
            st.session_state.duration,
            st.session_state.notes,
            bgg_game_id,
            st.session_state.username,
            st.session_state.join_me_by_default
        )

        telegram_bot.send_new_table_message(
            game_name,
            st.session_state.max_players,
            st.session_state.date.strftime('%Y-%m-%d'),
            time_option_to_time(st.session_state.time_option).strftime('%H:%M'),
            st.session_state.duration,
            st.session_state.username,
            last_row_id
        )

        refresh_table_propositions("Created")
        if st.session_state.join_me_by_default:
            st.toast(f"✅ Joined Table {last_row_id} as {st.session_state.username}!")
        st.toast(f"➕ Table proposition created successfully!\nTable ID: {last_row_id} - {game_name}")

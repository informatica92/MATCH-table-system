import streamlit as st

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_url

stu.add_title_text(st, frmt="{title}")

st.header("🎲 Owned Games")
st.write(
    "Browse and filter the board games **owned** by all the users of the system.\n\n"
    "The list is collected automatically from [BoardGameGeek](https://boardgamegeek.com/) for every "
    "user that has set a **BGG username** (see the **👦🏻 User** page). It is refreshed periodically and "
    "at every app startup."
)

owned_games_df = stu.get_all_owned_games(return_as_df=True)

if owned_games_df.empty:
    st.info(
        "No owned games have been collected yet.\n\n"
        "This can happen if no user has set a BGG username yet, or if the first synchronization with "
        "BoardGameGeek is still running (it runs one user per minute to respect BGG rate limits). "
        "Please check back later."
    )
    with st.sidebar:
        stu.add_powered_by_bgg_image()
        stu.add_donation_button()
    st.stop()

st.write(f":material/info: *Collection Last Update: {owned_games_df['last_updated'].max().strftime('%Y-%m-%d %H:%M:%S')}*")

# --- FILTERS ---
with st.container(border=True, gap="xxsmall"):
    st.subheader(":material/filter_alt: Filters")
    with st.container(border=False, horizontal=True, gap="medium"):
        owners = sorted([o for o in owned_games_df['owner_username'].dropna().unique().tolist()])
        selected_owners = st.multiselect(
            "Owners",
            options=owners,
            default=[],
            placeholder="All owners",
            help="Filter by the users who own the games"
        )

        name_query = st.text_input(
            "Game name contains",
            value="",
            placeholder="e.g. Wingspan",
            help="Case-insensitive search on the game name"
        )

        n_players = st.number_input(
            "Playable with N players",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            help="Keep only games whose min/max players range includes this number of players (0 = no filter)"
        )
        min_rating = st.slider(
            "Minimum average rating",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Keep only games with a BGG average rating greater than or equal to this value"
        )

# --- APPLY FILTERS ---
filtered_df = owned_games_df.copy()

if selected_owners:
    filtered_df = filtered_df[filtered_df['owner_username'].isin(selected_owners)]

if name_query:
    filtered_df = filtered_df[
        filtered_df['name'].fillna("").str.contains(name_query, case=False, regex=False)
    ]

if n_players and n_players > 0:
    filtered_df = filtered_df[
        (filtered_df['min_players'].fillna(0) <= n_players)
        & (filtered_df['max_players'].fillna(9999) >= n_players)
    ]

if min_rating and min_rating > 0:
    filtered_df = filtered_df[filtered_df['average_rating'].fillna(0) >= min_rating]

# --- SUMMARY METRICS ---
with st.container(border=True, horizontal=True, gap="xxsmall"):
    st.metric("Games shown", len(filtered_df))
    st.metric("Distinct titles", filtered_df['bgg_game_id'].nunique())
    st.metric("Owners shown", filtered_df['owner_username'].nunique())

# --- DISPLAY ---
display_df = filtered_df.copy()
display_df['bgg_url'] = display_df['bgg_game_id'].apply(lambda gid: get_bgg_url(gid) if gid is not None else None)

display_columns = [
    'thumbnail_url',
    'name',
    'year_published',
    'owner_username',
    'min_players',
    'max_players',
    'playing_time',
    'average_rating',
    'num_plays',
    'bgg_url',
]

st.dataframe(
    display_df[display_columns],
    hide_index=True,
    width='stretch',
    column_config={
        'thumbnail_url': st.column_config.ImageColumn("🖼️", help="Game thumbnail"),
        'name': st.column_config.TextColumn("Game"),
        'year_published': st.column_config.NumberColumn("Year", format="%d"),
        'owner_username': st.column_config.TextColumn("Owner"),
        'min_players': st.column_config.NumberColumn("Min P.", format="%d"),
        'max_players': st.column_config.NumberColumn("Max P.", format="%d"),
        'playing_time': st.column_config.NumberColumn("Time (min)", format="%d"),
        'average_rating': st.column_config.NumberColumn("Avg rating", format="%.1f"),
        'num_plays': st.column_config.NumberColumn("Plays", format="%d"),
        'bgg_url': st.column_config.LinkColumn("Link", display_text="Link")
    }
)

with st.sidebar:
    stu.add_powered_by_bgg_image()
    stu.add_donation_button()

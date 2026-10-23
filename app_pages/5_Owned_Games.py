import streamlit as st
from zoneinfo import ZoneInfo

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_url
from utils.altair_manager import get_bar_chart_from_grouped_df

METRICS_STATS_TOP_N = 3
GAME_TYPE_OPTIONS = {"boardgame": "Base", "boardgameexpansion": "Expansion"}

stu.add_title_text(st, frmt="{title}")

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

st.header(
    "🎲 Owned Games",
    help="Browse and filter the board games **owned** by all the users of the system.\n\n"
        "The list is collected automatically from [BoardGameGeek](https://boardgamegeek.com/) for every "
        "user that has set a **BGG username** (see the **👦🏻 User** page). \n\n"
        "It is refreshed periodically and "
        "at every app startup.\n\n"
)
## Collection Last Update (from the sync log: when the job last finished, not per-game last change)
tz = st.context.timezone
last_sync = stu.get_last_owned_games_sync()
if last_sync and last_sync.get('finished_at'):
    collection_last_update = last_sync['finished_at'].astimezone(ZoneInfo(tz)).strftime(f'%Y-%m-%d %H:%M ({tz})')
else:
    collection_last_update = "N/A"
st.badge(label=f"*Collection Last Update: {collection_last_update}*", color="blue", icon=":material/info:")

# --- FILTERS ---
filters_keys = ["owners", "name", "n_players", "min_rating", "game_type"]
num_active_filters = sum(
    [
        1 for k in filters_keys if st.session_state.get(k) or st.query_params.get(k)
    ]
)

with st.expander(f":material/filter_list: Filters ({num_active_filters})", key="filters_state"):
    with st.container(border=False, horizontal=True, gap="medium"):
        owners = sorted([o for o in owned_games_df['owner_username'].dropna().unique().tolist()])
        selected_owners = st.multiselect(
            ":material/people: Owners",
            options=owners,
            default=[],
            placeholder="All owners",
            help="Filter by the users who own the games",
            key="owners",
            bind="query-params"
        )

        name_query = st.text_input(
            ":material/search: Game name",
            value="",
            placeholder="e.g. Wingspan",
            help="Case-insensitive search on the game name",
            key="name",
            bind="query-params"
        )

        n_players = st.number_input(
            ":material/diversity_3: N players",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            help="Keep only games whose min/max players range includes this number of players (0 = no filter)",
            key="n_players",
            bind="query-params"
        )
        min_rating = st.number_input(
            ":material/star: Min rating",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Keep only games with a BGG average rating greater than or equal to this value",
            key="min_rating",
            bind="query-params"
        )

        game_types = st.multiselect(
            ":material/category: Type",
            placeholder="All types",
            options=GAME_TYPE_OPTIONS,
            default=[],
            format_func=lambda x: GAME_TYPE_OPTIONS[x],
            help="Filter by BGG type: base games vs expansions",
            key="game_type",
            bind="query-params"
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

if game_types:
    filtered_df = filtered_df[filtered_df['subtype'].isin(game_types)]

st.markdown(
    """
<style>
[data-testid="stMetricValue"] { font-size: 20px; }
[data-testid="stMetricLabel"] { font-size: 12px; }
[data-testid="stMetricDelta"] { font-size: 11px; }
""",
    unsafe_allow_html=True,
)
# --- SUMMARY METRICS ---
with st.container(horizontal=True, gap="xsmall", wrap=False):
    st.metric("Games", len(filtered_df), delta=f":material/compress: {filtered_df['bgg_game_id'].nunique()}", delta_color="off", delta_arrow="off", help="Number of games shown (above) and number of unique games (below)", width="content")
    st.metric("Owners", filtered_df['owner_username'].nunique(), width="content")
    st.altair_chart(get_bar_chart_from_grouped_df(filtered_df['name'].value_counts(), color="lightblue", x_label="# owners"))
    st.altair_chart(get_bar_chart_from_grouped_df(filtered_df.groupby(['name'])["num_plays"].sum().sort_values(ascending=False), color="lightgreen", x_label="# plays"))
    st.altair_chart(get_bar_chart_from_grouped_df(filtered_df['owner_username'].value_counts(), color="orange", x_label="# games"))

# --- DISPLAY ---
display_df = filtered_df.copy()
display_df['bgg_url'] = display_df['bgg_game_id'].apply(lambda gid: get_bgg_url(gid) if gid is not None else None)
display_df['is_expansion'] = display_df['subtype'] == 'boardgameexpansion'

display_columns = [
    'thumbnail_url',
    'name',
    'is_expansion',
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
        'is_expansion': st.column_config.CheckboxColumn("Exp.", help="Whether the game is an expansion (BGG subtype)"),
        'year_published': st.column_config.NumberColumn("Year", format="%d"),
        'owner_username': st.column_config.TextColumn("Owner"),
        'min_players': st.column_config.NumberColumn("Min P.", format="%d"),
        'max_players': st.column_config.NumberColumn("Max P.", format="%d"),
        'playing_time': st.column_config.NumberColumn("Time (min)", format="%d"),
        'average_rating': st.column_config.NumberColumn("Rating", format="%.1f"),
        'num_plays': st.column_config.NumberColumn("Plays", format="%d"),
        'bgg_url': st.column_config.LinkColumn("Link", display_text="Link")
    }
)

with st.sidebar:
    stu.add_powered_by_bgg_image()
    stu.add_donation_button()

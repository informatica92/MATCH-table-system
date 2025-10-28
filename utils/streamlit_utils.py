import os

import streamlit as st
from streamlit import components

import pandas as pd
from time import time as time_time, sleep
from datetime import datetime

from utils.telegram_notifications import TelegramNotifications
from utils.sql_manager import SQLManager
from utils.bgg_manager import get_bgg_url
from utils.table_system_proposition import TableProposition, JoinedPlayerOrProposer
from utils.table_system_logging import logging


DEFAULT_IMAGE_URL = "static/images/no_image.jpg"

BGG_GAME_ID_HELP = ("It's the id in the BGG URL. EX: for Wingspan the URL is "
                    "https://boardgamegeek.com/boardgame/266192/wingspan, hence the BGG game id is 266192")

# PAGES
VIEW_JOIN_BASE_MODULE = "app_pages.1_View_&_Join_Base"
VIEW_JOIN_LOC_DEFAULT_PAGE = "app_pages/1_View_&_Join_Loc_Default.py"
VIEW_JOIN_LOC_ROW_PAGE = "app_pages/1_View_&_Join_Loc_RoW.py"
VIEW_JOIN_PROPOSITIONS_PAGE = "app_pages/1_View_&_Join_Prop_00_Propositions.py"
VIEW_JOIN_TOURNAMENTS_PAGE = "app_pages/1_View_&_Join_Prop_01_Tournaments.py"
VIEW_JOIN_DEMOS_PAGE = "app_pages/1_View_&_Join_Prop_02_Demos.py"
CREATE_PAGE = "app_pages/2_Create.py"
MAP_PAGE = "app_pages/3_Map.py"
USER_PAGE = "app_pages/4_User.py"


CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;'>{label}</p>"

BOUNCE_SIDEBAR_ICON = r"""
    <style>
    .st-emotion-cache-169dgwr {
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
    
    .stAlert div {
        padding: 2px;
    }
    
    </style>
"""

sql_manager = SQLManager()
sql_manager.create_tables()

telegram_bot = TelegramNotifications()

def get_duration_step():
    return int(os.getenv("DURATION_MINUTES_STEP", 30))

def get_title():
    return os.environ.get("TITLE") or "Board Game Proposals"

def add_title_text(col, frmt="{title}"):
    col.title(frmt.format(title=get_title()))

def add_help_button(col: st.delta_generator.DeltaGenerator):
    col.write("")
    with col.popover("", icon="ℹ️", width='stretch'):
        st.write(f"Expanding the sidebar on the left ◀️ you can navigate among pages:\n\n"
         f"- **📜 Tables by ...**: view the table propositions, join, leave or edit them\n"
         f"   - **List**: view the table propositions as a list\n"
         f"   - **Timeline**: view the table propositions as a timeline\n"
         f"   - **Table**: view the table propositions as a table\n"
         f" - **➕ Create**: create a new table proposition\n"
         f" - **🗺️ Map**: view where the main location is and what is around there for food and drinks\n"
         f" - **👦🏻 User**: view the user profile (name, surname, username...) and manage locations\n\n"
         f"NB: *you have to set a **username** into the **\"User\"** page to join, create or edit tables*")

def get_logo():
    return os.environ.get("LOGO") or "images/logo.jpg"

def redirect_to_user_page_if_username_not_set():
    if st.session_state.user.is_logged_in() and not st.session_state['username']:
        st.switch_page("app_pages/4_User.py")

def get_go_to_user_page_link_button(use_container_width: bool = True):
    st.page_link(
        "app_pages/4_User.py",
        label="Go to \"**User**\" page",
        icon="🔗",
        width='content' if use_container_width is False else 'stretch',
    )

def st_write(label: str, size: int = 12) -> None:
    st.write(CUSTOM_TEXT_WITH_LABEL_AND_SIZE.format(label=label, size=size), unsafe_allow_html=True)

def str_to_bool(s: str) -> bool:
    """
    Convert a string to a boolean
    :param s: the string to convert
    :return:
    """
    return str(s).lower() == 'true'

def fake_space_for_horizontal_container(number=1):
    for _ in range(number):
        with st.container():
            st.empty()

def refresh_table_propositions(reason, **kwargs):
    """
    Refresh the table propositions in the session state
    :param reason: the reason why the refresh is needed (Init, Delete, Join...)
    :param kwargs: contextual information for the given reason (Delete: the deleted table id, Create: game name, table id...)
    :return:
    """
    query_start_time = time_time()

    if "joined_by_me" in st.session_state:
        joined_by_me = st.session_state.joined_by_me
    else:
        joined_by_me = False

    if "proposed_by_me" in st.session_state:
        proposed_by_me = st.session_state.proposed_by_me
    else:
        proposed_by_me = False

    # default, row
    location_mode = st.session_state.get("location_mode") or st.session_state.get("location_mode_filter")
    filter_default_location = {"default": True, "row": False}

    # 0 = Proposition, 1 = Tournament, 2 = Demo (the var1 or var2 syntax can not be used here since 0 is a valid value)
    proposition_type_id_mode = st.session_state.get("proposition_type_id_mode") if st.session_state.get("proposition_type_id_mode") is not None else st.session_state.get("proposition_type_id_mode_filter")

    st.session_state.global_propositions = TableProposition.from_list_of_tuples(sql_manager.get_table_propositions())
    st.session_state.propositions = st.session_state.global_propositions.copy()

    if joined_by_me:
        st.session_state.propositions = [tp for tp in st.session_state.propositions if tp.joined(st.session_state.user.user_id)]

    if proposed_by_me:
        st.session_state.propositions = [tp for tp in st.session_state.propositions if tp.proposed_by.user_id == st.session_state.user.user_id]

    # FILTER BY LOCATION
    if location_mode is not None:
        st.session_state.propositions = [tp for tp in st.session_state.propositions if tp.location.location_is_default is filter_default_location[location_mode]]

    # FILTER BY PROPOSITION TYPE
    if proposition_type_id_mode is not None:
        st.session_state.propositions = [tp for tp in st.session_state.propositions if tp.proposition_type_id == proposition_type_id_mode]

    logging.info(f"[User: {st.session_state.user if st.session_state.get('user') else '(not instantiated)'}] "
          f"Table propositions QUERY [{reason}] refreshed in {(time_time() - query_start_time):.4f}s "
          f"({len(st.session_state.propositions)} rows) "
          f"(context: {kwargs})")

def scroll_to(element_id):
    tmp = st.empty()
    with tmp:
        components.v1.html(f'''
            <script>
                var element = window.parent.document.getElementById("{element_id}");
                element.scrollIntoView({{behavior: 'smooth'}});
            </script>
        '''.encode())
        sleep(0.5)
    tmp.empty()

# TODO: evaluate chance to move it into TableProposition class
def check_overlaps_in_joined_tables(table_propositions:  list[TableProposition], current_user_id: int) -> tuple[list[tuple[TableProposition, TableProposition]], list[tuple[TableProposition, TableProposition]]]:
    joined_tables = [tp for tp in table_propositions if tp.joined(current_user_id)]
    # check if the start time and duration of the tables joined by the user (in joined_tables) contain any kind of
    # overlaps. In particular mark the cases in which the start date is exactly the same as ERROR and all the other
    # types of overlaps as warning
    # TableProposition fields: table_id, proposed_by_id, proposed_by_username, proposed_by_email, date, time, duration (h)
    # JoinedPlayerOrProposer fields: username, email
    errors_overlaps = []
    warnings_overlaps = []
    n = len(joined_tables)
    for i in range(n):
        tp = joined_tables[i]
        for j in range(i+1, n):
            tp2 = joined_tables[j]
            if tp.start_datetime <= tp2.start_datetime < tp.end_datetime or tp.start_datetime < tp2.end_datetime <= tp.end_datetime:
                if tp.start_datetime == tp2.start_datetime:
                    errors_overlaps.append((tp, tp2))
                else:
                    warnings_overlaps.append((tp, tp2))
    return errors_overlaps, warnings_overlaps

def render_overlaps_table_buttons(table_left, table_right, prefix):
    col1, col2 = st.columns([1, 1])
    def _render_overlaps_table_buttons(table_target, col):
        if table_target.table_id in [p.table_id for p in st.session_state.propositions]:
            if col.button(
                    f"Go to table {table_target.table_id}",
                    key=f"ov-{prefix}-{table_left.table_id}-{table_right.table_id}-{table_target.table_id}",
                    width='stretch',
                    disabled=True if st.session_state.get("view_mode") != "📜List" else False,
                    help="Only available in the '📜List' view mode"
            ):
                scroll_to(f"table-{table_target.table_id}")
        else:
            if col.button(
                    f"Go to {'Propositions' if table_target.proposition_type_id == 0 else 'Tournaments' if table_target.proposition_type_id == 1 else 'Demos'} page",
                    key=f"ov-{prefix}-{table_left.table_id}-{table_right.table_id}-{table_target.table_id}",
                    width='stretch'
            ):
                st.switch_page(
                    VIEW_JOIN_PROPOSITIONS_PAGE if table_target.proposition_type_id == 0 else
                    VIEW_JOIN_TOURNAMENTS_PAGE if table_target.proposition_type_id == 1 else
                    VIEW_JOIN_DEMOS_PAGE
                )
    _render_overlaps_table_buttons(table_left, col1)
    _render_overlaps_table_buttons(table_right, col2)

# All game names start with 'TOURNAMENT | ' or 'DEMO | ' if old proposition_type_id is 1 or 2 respectively,
# otherwise it's just the game name.
# Since now, we are updating the proposition_type_id, we need to check if the game name starts with
# 'TOURNAMENT | ' or 'DEMO | ' and remove it if necessary based on the new proposition_type_id.
def edit_game_name(game_name: str, old_proposition_type_id: int, new_proposition_type_id: int) -> str:

    if old_proposition_type_id == new_proposition_type_id:
        return game_name  # no change in proposition type, keep the same name
    else:
        # Remove optional prefix based on old proposition type and add new one if needed
        if old_proposition_type_id == 1:  # was TOURNAMENT
            game_name = game_name.replace("TOURNAMENT | ", "", 1)
        elif old_proposition_type_id == 2:  # was DEMO
            game_name = game_name.replace("DEMO | ", "", 1)
        # Add new prefix based on new proposition type
        if new_proposition_type_id == 1:  # is TOURNAMENT
            return f"TOURNAMENT | {game_name}"
        elif new_proposition_type_id == 2:  # is DEMO
            return f"DEMO | {game_name}"
        else:  # is PROPOSITION (0)
            return game_name

def update_table_propositions(
        old_table: TableProposition,
        game_name: str,
        max_players: int,
        date: datetime.date,
        time: datetime.time,
        duration: int,
        notes: str,
        bgg_game_id: int,
        location_id: int,
        expansions: list[dict] = None,
        proposition_type_id: int = None
):
    table_id = int(old_table.table_id)
    game_name = edit_game_name(game_name, old_table.proposition_type_id, proposition_type_id or 0)
    sql_manager.update_table_proposition(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, location_id, expansions, proposition_type_id)

    location_alias = get_available_locations(user_id=st.session_state.user.user_id, include_system_ones=True, return_as_df=True).set_index("id").loc[location_id, "alias"]
    location_is_default = is_default_location(location_id)
    expansions_name_list = [expansion['value'] for expansion in expansions] if expansions else []
    old_expansions_name_list = [expansion.expansion_name for expansion in old_table.expansions] if old_table.expansions else []

    telegram_bot.send_update_table_message(
        game_name=game_name,
        proposed_by=st.session_state.username,
        table_id=table_id,
        is_default_location=location_is_default,
        image_url=old_table.image_url if bgg_game_id else None,
        proposition_type_id=proposition_type_id,
        old_max_players=old_table.max_players,
        new_max_players=max_players,
        old_date=old_table.date.strftime('%Y-%m-%d'),
        new_date=date.strftime('%Y-%m-%d'),
        old_time=old_table.time.strftime('%H:%M'),
        new_time=time.strftime('%H:%M'),
        old_duration=old_table.duration,
        new_duration=duration,
        old_location_alias=old_table.location.location_alias if old_table.location else "Unknown",
        new_location_alias=location_alias if location_alias else "Unknown",
        old_notes=old_table.notes,
        new_notes=notes,
        old_expansions=old_expansions_name_list,
        new_expansions=expansions_name_list if expansions_name_list else [],
    )
    refresh_table_propositions("Table Update",table_id=table_id, game_name=game_name)

# TODO: evaluate chance to move it into TableProposition class (NB: add table_propositions as parameter)
def table_propositions_to_df(
        add_start_and_end_date=False, add_group=False, add_status=False,
        add_bgg_url=False, add_players_fraction=False, add_joined=False,
):
    df = pd.DataFrame(TableProposition.to_list_of_dicts(st.session_state.propositions, simple=True))

    if add_start_and_end_date:
        # concat date and time columns to get the start datetime
        df['start_datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
        # add 'duration' to 'start_datetime'
        df['end_datetime'] = df['start_datetime'] + pd.to_timedelta(df['duration'], unit='minute')

    if add_group:
        # 'Morning' if time.hour < 12 else 'Afternoon' if time.hour < 18 else 'Evening'
        df['group'] = df['time'].apply(lambda x: 'Morning' if x.hour < 12 else 'Afternoon' if x.hour < 18 else 'Evening')

    if add_status:
        df['status'] = df.apply(lambda x: 'Full' if x['joined_count'] == x['max_players'] else 'Available', axis=1)

    if add_bgg_url:
        df['bgg'] = df['bgg_game_id'].apply(get_bgg_url)

    if add_players_fraction:
        df['players'] = df['joined_count'].astype(str) + "/" + df['max_players'].astype(str)

    if add_joined:
        # check if st.session_state.username (str) is in the joined_players field (list[str])
        if st.session_state.username:
            df['joined'] = df['joined_players'].apply(lambda x: st.session_state.username.lower() in [player.lower() for player in x])
        else:
            df['joined'] = False

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

def can_current_user_delete_and_edit(proposed_by):
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

def join_callback(table_id, joining_username, joining_user_id):
    try:
        sql_manager.join_table(int(table_id), int(joining_user_id))
        refresh_table_propositions("Join", table_id=table_id)
        st.toast(f"✅ Joined Table {table_id} as {joining_username}!")
    except AttributeError as e :
        st.toast(f"🚫 {e}")
        refresh_table_propositions(reason="Error joining")


def leave_callback(table_id, leaving_username, leaving_user_id):
    sql_manager.leave_table(int(table_id), int(leaving_user_id))
    refresh_table_propositions("Leave", leaving_user=f"{leaving_username}({leaving_user_id})", table_id=table_id)
    st.toast(f"⛔ {leaving_username} left Table {table_id}")

def delete_callback(table_id):
    sql_manager.delete_proposition(int(table_id))
    refresh_table_propositions("Delete", table_id=table_id)
    st.toast(f"⛔ Deleted Table {table_id}")

def create_callback(game_name, bgg_game_id, image_url):
    if game_name:
        proposition_type_id = st.session_state.proposition_type['id'] if st.session_state.get('proposition_type') else 0  # 0 -> default type
        game_prefix = "" if proposition_type_id == 0 else f"{st.session_state.proposition_type['value'].upper()} | "
        last_row_id = sql_manager.create_proposition(
            f"{game_prefix}{game_name}",
            st.session_state.max_players,
            st.session_state.date,
            time_option_to_time(st.session_state.time_option),
            st.session_state.duration,
            st.session_state.notes,
            bgg_game_id,
            st.session_state.user.user_id,
            st.session_state.join_me_by_default,
            st.session_state.location[0] if st.session_state.location else None,  # location id,
            st.session_state.expansions,
            proposition_type_id
        )

        telegram_output = telegram_bot.send_new_table_message(
            f"{game_prefix}{game_name}",
            st.session_state.max_players,
            st.session_state.date.strftime('%Y-%m-%d'),
            time_option_to_time(st.session_state.time_option).strftime('%H:%M'),
            st.session_state.duration,
            st.session_state.username,
            last_row_id,
            is_default_location(st.session_state.location[0]) if st.session_state.location else True,
            st.session_state.location[1] if st.session_state.location else None,  # location alias
            image_url,
            proposition_type_id,
            st.session_state.notes,
            [e['value'] for e in st.session_state.expansions] if st.session_state.expansions else []
        )

        refresh_table_propositions("Created", table_id=last_row_id, game_name=f"{game_prefix}{game_name}", bgg_game_id=bgg_game_id)
        if st.session_state.join_me_by_default:
            st.toast(f"✅ Joined Table {last_row_id} as {st.session_state.username}!")
        st.toast(f"➕ Table proposition created successfully!\nTable ID: {last_row_id} - {game_name}")
        if not telegram_output.skipped:
            if telegram_output.message_id:
                st.toast(f"✅ Telegram notification sent successfully!")
            else:
                st.toast(f"🚫 Telegram notification failed: **{telegram_output.error}**")

def get_num_active_filters(as_str=True):
    number_of_active_filters = 0
    if st.session_state.get('joined_by_me', False):
        number_of_active_filters += 1
    if st.session_state.get('proposed_by_me', False):
        number_of_active_filters += 1
    if st.session_state.get('location_mode_filter') is not None or st.session_state.get('location_mode') is not None:
        number_of_active_filters += 1
    if st.session_state.get('proposition_type_id_mode_filter') is not None or st.session_state.get('proposition_type_id_mode') is not None:
        number_of_active_filters += 1
    filter_label_num_active_filters = "" if number_of_active_filters == 0 else f" ({number_of_active_filters}) "
    return filter_label_num_active_filters if as_str else number_of_active_filters

def _on_location_df_change(entire_locations_df: pd.DataFrame, user_id: int|None):

    list_of_dict_edited = st.session_state[f"data_editor_locations_df_{user_id}"]["edited_rows"]
    list_of_dict_added = st.session_state[f"data_editor_locations_df_{user_id}"]["added_rows"]
    list_of_dict_deleted = st.session_state[f"data_editor_locations_df_{user_id}"]["deleted_rows"]

    # added
    for row in list_of_dict_added:
        if row.get("street_name") and row.get("city") and row.get("house_number") and row.get("country") and row.get("alias"):
            sql_manager.add_user_location(user_id, row.get("street_name"), row.get("city"), row.get("house_number"), row.get("country"), row.get("alias"))
            st.toast(f"✅ Added location {row.get('alias')}")

    # updated
    edited_locations_df = []
    for index in list_of_dict_edited:
        tmp = entire_locations_df.iloc[index].to_dict()
        tmp.update(list_of_dict_edited[index])
        edited_locations_df.append(tmp)
    edited_locations_df = pd.DataFrame(edited_locations_df)
    sql_manager.update_user_locations(locations_df=edited_locations_df)

    # deleted
    ids_to_delete = []
    for row in list_of_dict_deleted:
        ids_to_delete.append(int(entire_locations_df.loc[row]["id"]))
    sql_manager.delete_locations(ids_to_delete)

    refresh_table_propositions("Location Update")

    if user_id:
        # clear user cache
        get_available_locations.clear(user_id, True, True)
        get_available_locations.clear(user_id, True, False)
        get_available_locations.clear(user_id, False, True)
        get_available_locations.clear(user_id, False, False)
    else:
        # clear all caches
        get_available_locations.clear()
        get_default_location.clear()

def manage_user_locations(user_id: int|None):
    df = get_available_locations(user_id, include_system_ones=True if not user_id else False, return_as_df=True)

    default_location = {}
    if user_id is None:
        # create a default_location var with the single row in the dataframe with the 'is_default' column set to True
        default_location: dict = df[df["is_default"] == True].to_dict(orient="records")[0]

    df = df[["id", "alias", "country", "city", "street_name", "house_number"]]

    column_config = {
        "id": st.column_config.NumberColumn(
            "ID",
            help="The location ID, it's automatically generated once you fulfill all the required fields in the row",
            width="small",
            default=None,
            required=True,
            disabled=True,
        ),
        "alias": st.column_config.TextColumn(
            "Alias",
            help="The alias of the location",
            width="medium",
            default=None,
            required=True,
        ),
        "country": st.column_config.TextColumn(
            "Country",
            help="The country of the location",
            width="small",
            default="Italia",
            required=True,
        ),
        "city": st.column_config.TextColumn(
            "City",
            help="The city of the location",
            width="medium",
            default=None,
            required=True,
        ),
        "street_name": st.column_config.TextColumn(
            "Street Name",
            help="The street name of the location",
            width="medium",
            default=None,
            required=True,
        ),
        "house_number": st.column_config.NumberColumn(
            "Street Number",
            help="The house number of the location",
            width="small",
            default=None,
            required=True,
        ),
    }

    st.data_editor(
        df,
        hide_index=True,
        width='stretch',
        disabled=["id"],
        num_rows="dynamic",
        key=f"data_editor_locations_df_{user_id}",
        on_change=_on_location_df_change,
        kwargs={"entire_locations_df": df, "user_id": user_id},
        column_config=column_config
    )

    if default_location:
        st.write(f"Default location: {default_location['alias']} (ID: {default_location['id']})")

def display_system_locations():
    system_locations = get_available_locations(None, True, True)
    system_locations["address"] = system_locations[['street_name', 'house_number', 'city']].agg(', '.join, axis=1)
    system_locations['pages'] = system_locations['is_default'].map(
        {
            True:  [f"📜{get_default_location()['alias']}"],
            False: [f"🌍{get_rest_of_the_world_page_name()}"]
        }
    )

    system_locations = system_locations[["alias", "pages", "address"]]
    system_locations = system_locations.style.map(lambda _: "font-weight: bold", subset=['alias'])

    st.dataframe(
        system_locations,  # this is a pandas Style object, can not be used to filter columns anymore, that's why we filtered them before
        hide_index=True,
        row_height=25,
        width='content',
        column_config={
            'alias': st.column_config.TextColumn("Alias", help="Alias of the location, used to identify the location"),
            'pages': st.column_config.ListColumn("Pages", help="Pages in which tables at this location are displayed"),
            'address': st.column_config.TextColumn("Address", help="Address of the location"),
        }
    )

@st.cache_data
def get_available_locations(user_id, include_system_ones=True, return_as_df=False):
    locations = sql_manager.get_user_locations(user_id, include_system_ones=include_system_ones, return_as_df=return_as_df)
    return locations

@st.cache_data
def get_default_location() -> dict:
    return sql_manager.get_default_location()

def is_default_location(location_id):
    return int(location_id) == int(get_default_location()["id"])

def get_table_proposition_types(as_list_of_dicts: bool = False, as_reversed_dict: bool = False):
    # check if only one of the parameter is True
    if as_list_of_dicts and as_reversed_dict:
        raise ValueError("Only one of the parameters 'as_list_of_dicts' or 'as_reversed_dict' can be True")

    table_proposition_types = SQLManager.TABLE_PROPOSITION_TYPES

    if not str_to_bool(os.getenv("CAN_ADMIN_CREATE_TOURNAMENT")):
        table_proposition_types = {k: v for k, v in table_proposition_types.items() if v != 1}

    if not str_to_bool(os.getenv("CAN_ADMIN_CREATE_DEMO")):
        table_proposition_types = {k: v for k, v in table_proposition_types.items() if v != 2}

    if as_list_of_dicts:
        return [{"id": v, "value": k} for k, v in table_proposition_types.items()]
    elif as_reversed_dict:
        return {v: k for k, v in table_proposition_types.items()}
    else:
        return table_proposition_types

def get_rest_of_the_world_page_name():
    return os.environ.get("REST_OF_THE_WORLD_PAGE_NAME") or "Rest of the World"

def add_powered_by_bgg_image():
    bgg_url = os.getenv("BGG_URL", "https://boardgamegeek.com/")
    bgg_powered_by_img = os.getenv("BGG_POWERED_BY_IMAGE", "https://cf.geekdo-images.com/HZy35cmzmmyV9BarSuk6ug__small/img/gbE7sulIurZE_Tx8EQJXnZSKI6w=/fit-in/200x150/filters:strip_icc()/pic7779581.png")
    st.markdown(f"[![Powered by BGG]({bgg_powered_by_img})]({bgg_url})")


def add_donation_button(label='Support me on Ko-fi', color='#29abe0'):
    user = os.environ.get("DONATION_USER", "informatica92")
    donations_are_active = str_to_bool(os.environ.get("DONATIONS_ARE_ACTIVE", default="False"))
    if donations_are_active:
        script = f"""
        <script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script>
        <script type='text/javascript'>kofiwidget2.init('{label}', '{color}', '{user}');kofiwidget2.draw();</script>
        """
        components.v1.html(script)

def create_user_info(user: JoinedPlayerOrProposer, label=None, icon=None):
    with st.expander(f"{icon or ''}{label or ''}{user.username}"):
        st.write(f"**BGG**: *coming soon* **Telegram**: *coming soon*")
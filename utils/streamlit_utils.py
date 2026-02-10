import os
from typing import Literal

import streamlit as st
from streamlit import components

from time import sleep
import datetime

from utils.telegram_notifications import TelegramNotifications
from utils.table_system_location import get_available_locations, is_default_location
from utils.sql_manager import SQLManager
from utils.table_system_proposition import TableProposition, JoinedPlayerOrProposer, StreamlitTablePropositions


DEFAULT_IMAGE_URL = "static/images/no_image.jpg"

BGG_POWERED_BY_IMAGE_DEFAULT = "https://cf.geekdo-images.com/HZy35cmzmmyV9BarSuk6ug__small/img/gbE7sulIurZE_Tx8EQJXnZSKI6w=/fit-in/200x150/filters:strip_icc()/pic7779581.png"
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

HELP_TEXT = "Expanding the sidebar on the left ◀️ you can navigate among pages:\n\n"\
"- **📜 Tables by ...**: view the table propositions, join, leave or edit them\n"\
"   - **List**: view the table propositions as a list\n"\
"   - **Timeline**: view the table propositions as a timeline\n"\
"   - **Table**: view the table propositions as a table\n"\
" - **➕ Create**: create a new table proposition\n"\
" - **🗺️ Map**: view where the main location is and what is around there for food and drinks\n"\
" - **👦🏻 User**: view the user profile (name, surname, username...) and manage locations\n\n"\
"NB: *you have to set a **username** into the **\"User\"** page to join, create or edit tables*"\

CUSTOM_TEXT_WITH_LABEL_AND_SIZE = "<p style='font-size:{size}px;color:{color}'>{label}</p>"

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

SPACE_BETWEEN_VERTICAL_COMPONENTS: Literal["xxsmall", "xsmall", "small", "medium", "large", "xlarge", "xxlarge"] = "xsmall"


sql_manager = SQLManager()
sql_manager.create_tables()

telegram_bot = TelegramNotifications()

def get_duration_step():
    return int(os.getenv("DURATION_MINUTES_STEP", 30))

def get_title():
    return os.environ.get("TITLE") or "Board Game Proposals"

def add_title_text(col, frmt="{title}"):
    col.title(frmt.format(title=get_title()), text_alignment="center", help=HELP_TEXT)

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

def st_write(label: str, size: int = 12, color: str = "black") -> None:
    txt = CUSTOM_TEXT_WITH_LABEL_AND_SIZE.format(label=label, size=size, color=color)
    st.write(txt, unsafe_allow_html=True)

def str_to_bool(s: str) -> bool:
    """
    Convert a string to a boolean
    :param s: the string to convert
    :return:
    """
    return str(s).lower() == 'true'

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
        bgg_game_id: int|str,
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
    StreamlitTablePropositions.refresh_table_propositions("Table Update",table_id=table_id, game_name=game_name)

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

def time_option_to_time(time_option):
    # time_option is a string with the following format "HH:MM - Morning|Afternoon|Evening|Night"
    time = datetime.datetime.strptime(time_option.split(" - ")[0], "%H:%M").time()
    return time

# CALLBACKS

def can_current_user_delete_and_edit(proposed_by):
    if st.session_state.god_mode:
        return True  # god mode can delete anything
    elif st.session_state.username and proposed_by.lower() == st.session_state.username.lower():
        return True  # table owner can remove their own tables
    else:
        return False

def join_callback(table_id, joining_username, joining_user_id):
    try:
        sql_manager.join_table(int(table_id), int(joining_user_id))
        StreamlitTablePropositions.refresh_table_propositions("Join", table_id=table_id)
        st.toast(f"✅ Joined Table {table_id} as {joining_username}!")
    except AttributeError as e :
        st.toast(f"🚫 {e}")
        StreamlitTablePropositions.refresh_table_propositions(reason="Error joining")

def leave_callback(table_id, leaving_username, leaving_user_id):
    sql_manager.leave_table(int(table_id), int(leaving_user_id))
    StreamlitTablePropositions.refresh_table_propositions("Leave", leaving_user=f"{leaving_username}({leaving_user_id})", table_id=table_id)
    st.toast(f"⛔ {leaving_username} left Table {table_id}")

def delete_callback(table_id):
    sql_manager.delete_proposition(int(table_id))
    StreamlitTablePropositions.refresh_table_propositions("Delete", table_id=table_id)
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
            is_default_location(st.session_state.location),
            st.session_state.location[1] if st.session_state.location else None,  # location alias
            image_url,
            proposition_type_id,
            st.session_state.notes,
            [e['value'] for e in st.session_state.expansions] if st.session_state.expansions else []
        )

        StreamlitTablePropositions.refresh_table_propositions("Created", table_id=last_row_id, game_name=f"{game_prefix}{game_name}", bgg_game_id=bgg_game_id)
        if st.session_state.join_me_by_default:
            st.toast(f"✅ Joined Table {last_row_id} as {st.session_state.username}!")
        st.toast(f"➕ Table proposition created successfully!\nTable ID: {last_row_id} - {game_name}")
        if not telegram_output.skipped:
            if telegram_output.message_id:
                st.toast(f"✅ Telegram notification sent successfully!")
            else:
                st.toast(f"🚫 Telegram notification failed: **{telegram_output.error}**")
        st.session_state.last_created_table_id = last_row_id

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
    bgg_powered_by_img = os.getenv("BGG_POWERED_BY_IMAGE", BGG_POWERED_BY_IMAGE_DEFAULT)
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
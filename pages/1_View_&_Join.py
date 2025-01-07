import streamlit as st

from time import time as time_time

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_game_info, get_bgg_url
from utils.altair_manager import timeline_chart


# # FEATURES
# TODO: use multi_pages -> https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app
# TODO: use st.cache_data for bgg info
# TODO: add "location" (system or user) into the Create (system locations => no user id)
# # IMPROVEMENTS
# TODO: use @st.fragments
# TODO: replace text+bgg search with: https://pypi.org/project/streamlit-searchbox/ (st.link_button) (requires no streamlit_extras => no cookies)
# TODO: link user table to joined_players and table_propositions
#   TODO: joined_players table -> change player_name to FK to users.id
#   TODO: change the get_table_propositions query to keep the same structure but joining now joined_players and users
#   TODO: table_propositions table -> change proposed_by to FK to users.id
#   TODO: change the leave_table to remove row using user_id instead of player_name
#   TODO: change the join_table to add row using user_id instead of player_name


@st.dialog("🖋️ Edit Table")
def dialog_edit_table_proposition(table_id, old_name, old_max_players, old_date, old_time, old_duration, old_notes, old_bgg_game_id, joined_count, old_location_alias):
    with st.form(key=f"form-edit-{table_id}"):
        col1, col2 = st.columns([1, 1])
        with col1:
            game_name = st.text_input("Game Name", value=old_name, disabled=True)
            max_players = st.number_input("Max Players", value=old_max_players, step=1, min_value=joined_count)
            date = st.date_input("Date", value=old_date)
        with col2:
            bgg_game_id = st.text_input("BGG Game ID", value=old_bgg_game_id, help=stu.BGG_GAME_ID_HELP, disabled=True)
            duration = st.number_input("Duration (hours)", value=old_duration, step=1)
            time = st.time_input("Time", value=old_time, step=60*30)

        # locations
        locations = stu.get_available_locations(st.session_state.user.user_id)  # 'id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id'
        locations = [(loc[0], loc[5]) for loc in locations]
        location_old_index = None
        for i, (_, alias) in enumerate(locations):
            if alias == old_location_alias:
                location_old_index = i
        st.selectbox("Location", options=locations, index=location_old_index, key="location_edit", format_func=lambda x: x[1])

        notes = st.text_area("Notes", value=old_notes)

        submitted = st.form_submit_button("💾 Update")
        if submitted:
            stu.update_table_propositions(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, st.session_state.location_edit[0] if st.session_state.location_edit else None)
            st.rerun()

@st.dialog("⛔ Delete Proposition")
def dialog_delete_table_proposition(table_id: int, game_name: str, joined_count: int, joined_players: list, proposed_by:str):
    with st.form(key=f"form-delete-{table_id}"):
        st.write(f"Please, confirm you want to delete Table {table_id}:")
        st.write(f"**{game_name}**")

        if joined_count:
            joined_players_markdown = '\n\t - '  + '\n\t - '.join(joined_players)
            st.write(f"Details:\n "
                     f"- proposed by **{proposed_by}**\n "
                     f"- with {joined_count} player(s): {joined_players_markdown}\n ")
        else:
            st.write(f"Details:\n "
                     f"- proposed by **{proposed_by}**\n "
                     f"- without any joined player\n ")
        st.write("")
        submitted = st.form_submit_button("⛔ Yes, delete table and its joined player(s)")
        if submitted:
            stu.delete_callback(table_id)
            st.rerun()

def display_table_proposition(section_name, compact, table_id, game_name, bgg_game_id, proposed_by, max_players, date, time, duration, notes, joined_count, joined_players, joined_players_ids, location_alias, location_address, location_is_system):
    # Check if the BGG game ID is valid and set the BGG URL
    if bgg_game_id and int(bgg_game_id) >= 1:
        bgg_url = get_bgg_url(bgg_game_id)
        st.subheader(f"Table {table_id}: [{game_name}]({bgg_url})", anchor=f"table-{table_id}")
    else:
        st.subheader(f"Table {table_id}: {game_name}", anchor=f"table-{table_id}")

    # Create three columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if bgg_game_id and int(bgg_game_id) >= 1:
            image_url, game_description, categories, mechanics, _ = get_bgg_game_info(bgg_game_id)
            image_width = 300 if not compact else 150
            caption = f"{game_description[:120]}..." if not compact else None
            if not image_url:
                image_url = stu.DEFAULT_IMAGE_URL
            st.image(image_url, width=image_width, caption=caption)
            if not compact:
                stu.st_write(
                    f"<b>Categories:</b> {', '.join(categories)}<br>"
                    f"<b>Mechanics:</b> {', '.join(mechanics)}"
                )
        else:
            st.image(stu.DEFAULT_IMAGE_URL)

    with col2:
        if not compact:
            st.write(f"**Proposed By:**&nbsp;{proposed_by}")
            st.write(f"**Max Players:**&nbsp;&nbsp;{max_players}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time.strftime('%H:%M')}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")
            if location_alias:
                st.write(f"**Location:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[{location_alias}](https://google.it/maps/place/{location_address.replace(' ', '+')})")
            st.write(f"**Notes:**")
            st.write(notes)
        else:
            st.write(f"**Proposed By:**&nbsp;{proposed_by}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{date} {time}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{duration} hours")

    with col3:
        is_full = joined_count >= max_players
        st.write(f":{'red' if is_full else 'green'}[**Joined Players ({joined_count}/{max_players}):**]")
        for joined_player, joined_player_id in zip(joined_players, joined_players_ids) or []:
            if joined_player is not None:
                player_col1, player_col2 = st.columns([1, 1])
                with player_col1:
                    st.write(f"- {joined_player}")
                with player_col2:
                    # LEAVE
                    st.button(
                        "⛔ Leave",
                        key=f"leave_{table_id}_{joined_player}_{section_name}",
                        on_click=stu.leave_callback, args=[table_id, joined_player, joined_player_id],
                        disabled=not stu.can_current_user_leave(joined_player, proposed_by),
                        help="Only the table owner or the player himself can leave a table."
                    )

    # Create four columns for action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if not is_full:
            if st.session_state['username']:
                st.button(
                    # JOIN
                    f"✅ Join Table {table_id}" if not stu.username_in_joined_players(joined_players) else "✅ *Already joined*",
                    key=f"join_{table_id}_{section_name}",
                    use_container_width=True,
                    disabled=stu.username_in_joined_players(joined_players),
                    on_click=stu.join_callback, args=[table_id, st.session_state['username'], st.session_state.user.user_id]
                )
            else:
                st.warning("Set a username to join a table.")
        else:
            st.warning(f"Table {table_id} is full.", )

    with col2:
        # DELETE
        if st.button(
            "⛔ Delete proposition",
            key=f"delete_{table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(proposed_by),
            help="Only the table owner can delete their tables."
        ):
            dialog_delete_table_proposition(table_id, game_name, joined_count, joined_players, proposed_by)
    with col3:
        if st.button(
            "🖋️ Edit",
            key=f"edit_{table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(proposed_by),
            help="Only the table owner can edit their tables."
        ):
            dialog_edit_table_proposition(table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, joined_count, location_alias)

    with col4:
        pass

def view_table_propositions(compact=False):
    for proposition in st.session_state.propositions:
        (table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, proposed_by_user_id, proposed_by,
         joined_count, joined_players, joined_players_ids, loc_alias, loc_address, loc_is_system) = proposition
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
            joined_players=joined_players,
            joined_players_ids=joined_players_ids,
            location_alias=loc_alias,
            location_address=loc_address,
            location_is_system=loc_is_system
        )

def timeline_table_propositions(compact=False):
    df = stu.table_propositions_to_df(add_group=True, add_status=True, add_start_and_end_date=True)

    chart = timeline_chart(df)
    selected_data = st.altair_chart(chart, use_container_width=True, on_select="rerun", theme=None)

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
                joined_players=selected_row['joined_players'],
                joined_players_ids=selected_row['joined_players_ids'],
                location_alias=selected_row['location_alias'],
                location_address=selected_row['location_address'],
                location_is_system=selected_row['location_is_system']
            )

def dataframe_table_propositions(compact=False):

    default_columns = ['image', 'time', 'game_name', 'duration', 'players', 'proposed_by', 'joined', 'bgg']
    all_columns = ['table_id', 'image', 'time', 'game_name', 'duration', 'date', 'players', 'joined_players', 'proposed_by', 'joined', 'bgg']
    st.multiselect("Columns", options=all_columns, default=default_columns, key="columns_order")

    df = stu.table_propositions_to_df(add_image_url=True, add_bgg_url=True, add_players_fraction=True, add_joined=True)

    column_config = {
        "table_id":  st.column_config.TextColumn("ID", width="small"),
        "image": st.column_config.ImageColumn("Image", width="small"),
        "bgg":  st.column_config.LinkColumn("BGG", display_text="link"),
        "date":  st.column_config.DateColumn("Date"),
        "time": st.column_config.TimeColumn("Time", format='HH:mm'),
        "duration": st.column_config.NumberColumn("Duration", format="%dh", width="small"),
        "players": st.column_config.TextColumn("Players"),
        "joined_players": st.column_config.ListColumn("Joined Players"),
        "game_name": st.column_config.TextColumn("Name"),
        "proposed_by": st.column_config.TextColumn("Proposed By"),
        "joined": st.column_config.CheckboxColumn("Joined", width="small")
    }

    selected_data = st.dataframe(df, hide_index=True, use_container_width=True, column_config=column_config, column_order=st.session_state.columns_order, on_select="rerun", selection_mode="single-row")

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("rows", {}) and len(selected_data["selection"]["rows"]) != 0:
            _id = selected_data["selection"]["rows"][0]
            selected_row = df.iloc[_id]
            display_table_proposition(
                section_name="timeline",
                compact=compact,
                table_id=int(selected_row['table_id']),
                game_name=selected_row['game_name'],
                bgg_game_id=selected_row['bgg_game_id'],
                proposed_by=selected_row['proposed_by'],
                max_players=selected_row['max_players'],
                date=selected_row['date'],
                time=selected_row['time'],
                duration=selected_row['duration'],
                notes=selected_row['notes'],
                joined_count=selected_row['joined_count'],
                joined_players=selected_row['joined_players'],
                joined_players_ids=selected_row['joined_players_ids'],
                location_alias=selected_row['location_alias'],
                location_address=selected_row['location_address'],
                location_is_system=selected_row['location_is_system']
            )


st.title(f"{stu.get_title()}")

with st.sidebar:
    with st.container(border=True):
        st.selectbox("View mode", options=["📜List", "📊Timeline", "◻️Table"], key="view_mode")
        st.toggle("Compact view", key="compact_view")

view_start_time = time_time()

refresh_col, filter_col, fake_col = st.columns([1, 1, 4])
with refresh_col:
    refresh_button = st.button("🔄️ Refresh", key="refresh", use_container_width=True)
    if refresh_button:
        stu.refresh_table_propositions("Refresh")
with filter_col:
    filter_label_num_active_filters = stu.get_num_active_filters(as_str=True)
    with st.popover(f"🔍 {filter_label_num_active_filters}Filters:", use_container_width=True):
        st.toggle("Joined by me", key="joined_by_me", value=False, on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering"}, disabled=not st.session_state['username'])

if len(st.session_state.propositions) == 0:
    st.info("No table propositions available, use the \"**➕Create**\" page to create a new one."
            "\n\n*NB: tables are automatically hidden after 1 day*")
else:
    if st.session_state['view_mode'] == "📜List":
        view_table_propositions(st.session_state['compact_view'])
    elif st.session_state['view_mode'] == "📊Timeline":
        timeline_table_propositions(st.session_state['compact_view'])
    else:
        dataframe_table_propositions(st.session_state['compact_view'])

print(f"Table propositions VIEW refreshed in {(time_time() - view_start_time):2f}s")

import streamlit as st

from time import time as time_time

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_game_info, get_bgg_url
from utils.altair_manager import timeline_chart
from utils.table_system_proposition import TableProposition, TablePropositionExpansion


@st.dialog("🖋️ Edit Table")
def dialog_edit_table_proposition(old_table_proposition: TableProposition):
    with st.form(key=f"form-edit-{old_table_proposition.table_id}"):
        col1, col2 = st.columns([1, 1])
        with col1:
            game_name = st.text_input("Game Name", value=old_table_proposition.game_name, disabled=True)
            max_players = st.number_input("Max Players", value=old_table_proposition.max_players, step=1, min_value=old_table_proposition.joined_count)
            date = st.date_input("Date", value=old_table_proposition.date)
        with col2:
            bgg_game_id = st.text_input("BGG Game ID", value=old_table_proposition.bgg_game_id, help=stu.BGG_GAME_ID_HELP, disabled=True)
            duration = st.number_input("Duration (hours)", value=old_table_proposition.duration, step=1)
            time = st.time_input("Time", value=old_table_proposition.time, step=60*30)

        # locations
        locations = stu.get_available_locations(st.session_state.user.user_id)  # 'id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id'
        locations = [(loc[0], loc[5]) for loc in locations]
        location_old_index = None
        for i, (_, alias) in enumerate(locations):
            if alias == old_table_proposition.location.location_alias:
                location_old_index = i
        st.selectbox("Location", options=locations, index=location_old_index, key="location_edit", format_func=lambda x: x[1])

        # expansions
        expansions_options = get_bgg_game_info(bgg_game_id)[4]
        expansions_default = TablePropositionExpansion.to_list_of_dicts(old_table_proposition.expansions)
        st.multiselect("Expansions", options=expansions_options, default=expansions_default, format_func=lambda x: x['value'], key="expansions_edit")

        # notes
        notes = st.text_area("Notes", value=old_table_proposition.notes)

        submitted = st.form_submit_button("💾 Update")
        if submitted:
            stu.update_table_propositions(old_table_proposition.table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, st.session_state.location_edit[0] if st.session_state.location_edit else None, st.session_state.expansions_edit)
            st.rerun()

@st.dialog("⛔ Delete Proposition")
def dialog_delete_table_proposition(table_proposition: TableProposition):
    with st.form(key=f"form-delete-{table_proposition.table_id}"):
        st.write(f"Please, confirm you want to delete Table {table_proposition.table_id}:")
        st.write(f"**{table_proposition.game_name}**")

        if table_proposition.joined_count:
            joined_players_markdown = '\n\t - '  + '\n\t - '.join(table_proposition.get_joined_players_usernames())
            st.write(f"Details:\n "
                     f"- proposed by **{table_proposition.proposed_by.username}**\n "
                     f"- with {table_proposition.joined_count} player(s): {joined_players_markdown}\n ")
        else:
            st.write(f"Details:\n "
                     f"- proposed by **{table_proposition.proposed_by.username}**\n "
                     f"- without any joined player\n ")
        st.write("")
        submitted = st.form_submit_button("⛔ Yes, delete table and its joined player(s)")
        if submitted:
            stu.delete_callback(table_proposition.table_id)
            st.rerun()

def display_table_proposition(section_name, compact, table_proposition: TableProposition):
    # Check if the BGG game ID is valid and set the BGG URL
    if table_proposition.bgg_game_id and int(table_proposition.bgg_game_id) >= 1:
        bgg_url = get_bgg_url(table_proposition.bgg_game_id)
        st.subheader(f"Table {table_proposition.table_id}: [{table_proposition.game_name}]({bgg_url})", anchor=f"table-{table_proposition.table_id}")
    else:
        st.subheader(f"Table {table_proposition.table_id}: {table_proposition.game_name}", anchor=f"table-{table_proposition.table_id}")

    # Create three columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if table_proposition.bgg_game_id and int(table_proposition.bgg_game_id) >= 1:
            image_url, game_description, categories, mechanics, _ = get_bgg_game_info(table_proposition.bgg_game_id)
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
            st.write(f"**Proposed By:**&nbsp;{table_proposition.proposed_by.username}")
            st.write(f"**Max Players:**&nbsp;&nbsp;{table_proposition.max_players}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.date} {table_proposition.time.strftime('%H:%M')}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.duration} hours")
            location_markdown = stu.get_location_markdown_text(table_proposition.location)
            st.write(f"**Location:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{location_markdown}")
            expansions_markdown = stu.get_expansions_markdown_text(table_proposition.expansions)
            st.write(f"**Expansions:** {expansions_markdown}")
            st.write(f"**Notes:**")
            st.write(table_proposition.notes)
        else:
            st.write(f"**Proposed By:**&nbsp;{table_proposition.proposed_by.username}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.date} {table_proposition.time}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.duration} hours")

    with col3:
        is_full = table_proposition.joined_count >= table_proposition.max_players
        st.write(f":{'red' if is_full else 'green'}[**Joined Players ({table_proposition.joined_count}/{table_proposition.max_players}):**]")
        for joined_player_obj in table_proposition.joined_players or []:
            if joined_player_obj.username is not None:
                player_col1, player_col2 = st.columns([1, 1])
                with player_col1:
                    st.write(f"- {joined_player_obj.username}")
                with player_col2:
                    # LEAVE
                    st.button(
                        "⛔ Leave",
                        key=f"leave_{table_proposition.table_id}_{joined_player_obj.username}_{section_name}",
                        on_click=stu.leave_callback, args=[table_proposition.table_id, joined_player_obj.username, joined_player_obj.user_id],
                        disabled=not stu.can_current_user_leave(joined_player_obj.username, table_proposition.proposed_by.username),
                        help="Only the table owner or the player himself can leave a table."
                    )

    # Create four columns for action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if not is_full:
            if st.session_state['username']:
                st.button(
                    # JOIN
                    f"✅ Join Table {table_proposition.table_id}" if not stu.username_in_joined_players(table_proposition.joined_players) else "✅ *Already joined*",
                    key=f"join_{table_proposition.table_id}_{section_name}",
                    use_container_width=True,
                    disabled=stu.username_in_joined_players(table_proposition.joined_players),
                    on_click=stu.join_callback, args=[table_proposition.table_id, st.session_state['username'], st.session_state.user.user_id]
                )
            else:
                if st.session_state.user.is_logged_in():
                    st.warning("Set a username to join a table.")
                else:
                    st.warning("**Log in** to join a table.")
        else:
            st.warning(f"Table {table_proposition.table_id} is full.", )

    with col2:
        # DELETE
        if st.button(
            "⛔ Delete proposition",
            key=f"delete_{table_proposition.table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(table_proposition.proposed_by.username),
            help="Only the table owner can delete their tables."
        ):
            dialog_delete_table_proposition(table_proposition)
    with col3:
        if st.button(
            "🖋️ Edit",
            key=f"edit_{table_proposition.table_id}_{section_name}",
            use_container_width=True,
            disabled=not stu.can_current_user_delete_and_edit(table_proposition.proposed_by.username),
            help="Only the table owner can edit their tables."
        ):
            dialog_edit_table_proposition(table_proposition)

    with col4:
        pass

def view_table_propositions(compact=False):
    for proposition in st.session_state.propositions:
        proposition: TableProposition
        display_table_proposition(section_name="list", compact=compact, table_proposition=proposition)

def timeline_table_propositions(compact=False):
    df = stu.table_propositions_to_df(add_group=True, add_status=True, add_start_and_end_date=True)

    chart = timeline_chart(df)
    selected_data = st.altair_chart(chart, use_container_width=True, on_select="rerun", theme=None)

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("param_1", {}) and len(selected_data["selection"]["param_1"]) != 0:
            _id = selected_data["selection"]["param_1"][0]['table_id']
            selected_row = df[df['table_id'] == _id].iloc[0]
            display_table_proposition(section_name="timeline", compact=compact, table_proposition=TableProposition.from_dict(selected_row))

def dataframe_table_propositions(compact=False):

    default_columns = ['image', 'time', 'game_name', 'duration', 'players', 'proposed_by_username', 'joined', 'bgg']
    all_columns = ['table_id', 'image', 'time', 'game_name', 'duration', 'date', 'players', 'joined_players', 'proposed_by_username', 'joined', 'bgg']
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
        "proposed_by_username": st.column_config.TextColumn("Proposed By"),
        "joined": st.column_config.CheckboxColumn("Joined", width="small")
    }

    selected_data = st.dataframe(df, hide_index=True, use_container_width=True, column_config=column_config, column_order=st.session_state.columns_order, on_select="rerun", selection_mode="single-row")

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("rows", {}) and len(selected_data["selection"]["rows"]) != 0:
            _id = selected_data["selection"]["rows"][0]
            selected_row = df.iloc[_id]
            display_table_proposition(section_name="timeline", compact=compact, table_proposition=TableProposition.from_dict(selected_row))

def create_view_and_join_page():

    # redirect to "User" page if username is not set
    stu.redirect_to_user_page_if_username_not_set()

    # title and help button
    col_title, col_help = st.columns([9, 1])
    stu.add_title_text(col_title, frmt="{title}")
    stu.add_help_button(col_help)

    # print(f"Location mode [View Page]: {st.session_state.location_mode}")

    # additional sidebar widgets
    with st.sidebar:
        with st.container(border=True):
            st.selectbox("View mode", options=["📜List", "📊Timeline", "◻️Table"], key="view_mode")
            st.toggle("Compact view", key="compact_view")

    # refresh and filter buttons
    refresh_col, filter_col, fake_col = st.columns([1, 1, 4])
    with refresh_col:
        refresh_button = st.button("🔄️ Refresh", key="refresh", use_container_width=True)
        if refresh_button:
            stu.refresh_table_propositions("Refresh")
    with filter_col:
        filter_label_num_active_filters = stu.get_num_active_filters(as_str=True)
        with st.popover(f"🔍 {filter_label_num_active_filters}Filters:", use_container_width=True):
            st.toggle("Joined by me", key="joined_by_me", value=False, on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering"}, disabled=not st.session_state['username'])

    # show propositions
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

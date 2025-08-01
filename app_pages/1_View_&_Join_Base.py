import streamlit as st

from time import time as time_time
import datetime

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_url
from utils.altair_manager import timeline_chart
from utils.table_system_proposition import TableProposition, TablePropositionExpansion


@st.dialog("🖋️ Edit Table")
def dialog_edit_table_proposition(old_table_proposition: TableProposition):
    with st.form(key=f"form-edit-{old_table_proposition.table_id}"):
        col1, col2 = st.columns([1, 1])
        with col1:
            game_name = st.text_input("Game Name", value=old_table_proposition.game_name, disabled=True)
            max_players = st.number_input("Max Players", value=old_table_proposition.max_players, step=1, min_value=old_table_proposition.joined_count)
            date = st.date_input("Date", value=old_table_proposition.date, min_value=min(old_table_proposition.date, datetime.date.today()))
        with col2:
            bgg_game_id = st.text_input("BGG Game ID", value=old_table_proposition.bgg_game_id, help=stu.BGG_GAME_ID_HELP, disabled=True)
            duration = st.number_input(f"Duration (minutes, step: {stu.get_duration_step()}mins)", value=old_table_proposition.duration, step=stu.get_duration_step())
            time = st.time_input("Time", value=old_table_proposition.time, step=60*30)

        # locations
        locations = stu.get_available_locations(st.session_state.user.user_id, True, False)  # 'id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id'
        locations = [(loc[0], loc[5]) for loc in locations]
        location_old_index = None
        for i, (_, alias) in enumerate(locations):
            if alias == old_table_proposition.location.location_alias:
                location_old_index = i
        st.selectbox("Location", options=locations, index=location_old_index, key="location_edit", format_func=lambda x: x[1])

        # expansions
        expansions_options = TablePropositionExpansion.to_list_of_dicts(old_table_proposition.available_expansions)
        expansions_default = TablePropositionExpansion.to_list_of_dicts(old_table_proposition.expansions)
        st.multiselect("Expansions", options=expansions_options, default=expansions_default, format_func=lambda x: x['value'], key="expansions_edit")

        # notes
        notes = st.text_area("Notes", value=old_table_proposition.notes)

        # table proposition type
        if st.session_state.user.is_admin:
            propositions_types = stu.get_table_proposition_types(as_list_of_dicts=True)
            # in case the old proposition type is not in the list, we set it to 0 (default => Proposition) that is always present
            index = old_table_proposition.proposition_type_id if old_table_proposition.proposition_type_id in [pt['id'] for pt in propositions_types] else 0
            st.selectbox("Proposition Type", options=propositions_types, key="proposition_type_edit", format_func=lambda x: x["value"], index=index)

        submitted = st.form_submit_button("💾 Update")
        if submitted:
            stu.update_table_propositions(old_table_proposition, game_name, max_players, date, time, duration, notes, bgg_game_id, st.session_state.location_edit[0] if st.session_state.location_edit else None, st.session_state.expansions_edit, st.session_state.proposition_type_edit['id'])
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
            # image_url, game_description, categories, mechanics, _, _ = get_bgg_game_info(table_proposition.bgg_game_id)
            image_width = 300 if not compact else 150
            caption = f"{table_proposition.game_description[:120]}..." if not compact else None
            st.image(table_proposition.image_url or stu.DEFAULT_IMAGE_URL, width=image_width, caption=caption)
            if not compact:
                stu.st_write(
                    f"<b>Categories:</b> {', '.join(table_proposition.categories)}<br>"
                    f"<b>Mechanics:</b> {', '.join(table_proposition.mechanics)}"
                )
        else:
            st.image(stu.DEFAULT_IMAGE_URL)

    with col2:
        def reset_table_info(key: str):
            st.session_state[key] = None

        st.pills(
            label="table_info", label_visibility="collapsed",
            options=[
                # f"🧑‍🤝‍🧑 {table_proposition.max_players} players",
                f"⌚ **{table_proposition.time.strftime('%H:%M')}**",
                f"📅 {table_proposition.date}",
                f"⏳ {'{:02d}:{:02d}'.format(*divmod(table_proposition.duration, 60))}h",
            ],
            key=f"table_info_{table_proposition.table_id}_{section_name}",
            on_change=reset_table_info, kwargs={"key": f"table_info_{table_proposition.table_id}_{section_name}"},
        )
        if not compact:
            with st.expander(f"🧔🏻 **Proposed By**: {table_proposition.proposed_by.username}"):
                st.write(f"**BGG**: *coming soon* **Telegram**: *coming soon*")
            with st.expander(f"🗺️ **Location**: {table_proposition.location.location_alias}"):
                location_markdown = table_proposition.location.to_markdown(st.session_state.user, icon="🔗")
                # location_markdown includes address + link to google maps IF default location or logged users
                # otherwise it is equal to "*Unknown*"
                st.write(location_markdown)
            with st.expander(f"📦 **Expansions** ({len(table_proposition.expansions)}):"):
                expansions_markdown = TablePropositionExpansion.to_markdown_list(table_proposition.expansions)
                st.write(expansions_markdown)
            notes_preview = f"*{table_proposition.notes[:30]}...*" if len(str(table_proposition.notes)) > 30 else table_proposition.notes
            with st.expander(f"📒 **Notes**: {notes_preview}"):
                st.write(table_proposition.notes)
        else:
            st.write(f"**Proposed By:**&nbsp;{table_proposition.proposed_by.username}")
            st.write(f"**Date Time:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.date} {table_proposition.time}")
            st.write(f"**Duration:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{table_proposition.duration} mins")

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
                    f"✅ Join Table {table_proposition.table_id}" if not table_proposition.joined(st.session_state.user.user_id) else "✅ *Already joined*",
                    key=f"join_{table_proposition.table_id}_{section_name}",
                    use_container_width=True,
                    disabled=table_proposition.joined(st.session_state.user.user_id),
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

    df = stu.table_propositions_to_df(add_bgg_url=True, add_players_fraction=True, add_joined=True)

    column_config = {
        "table_id":  st.column_config.TextColumn("ID", width="small"),
        "image_url": st.column_config.ImageColumn("Image", width="small"),
        "bgg":  st.column_config.LinkColumn("BGG", display_text="link"),
        "date":  st.column_config.DateColumn("Date"),
        "time": st.column_config.TimeColumn("Time", format='HH:mm'),
        "duration": st.column_config.NumberColumn("Duration", format="%dmin", width="small"),
        "players": st.column_config.TextColumn("Players"),
        "joined_players": st.column_config.ListColumn("Joined Players"),
        "game_name": st.column_config.TextColumn("Name"),
        "proposed_by_username": st.column_config.TextColumn("Proposed By"),
        "joined": st.column_config.CheckboxColumn("Joined", width="small")
    }
    # 'table_id', 'image', 'time', 'game_name', 'duration', 'date', 'players', 'joined_players', 'proposed_by_username', 'joined', 'bgg'
    columns_order =  ['table_id', 'image_url', 'date', 'time', 'game_name', 'duration', 'players', 'proposed_by_username', 'joined', 'bgg', 'joined_players']
    selected_data = st.dataframe(df, hide_index=True, use_container_width=True, column_config=column_config, column_order=columns_order, on_select="rerun", selection_mode="single-row", row_height=50)

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
        stu.add_donation_button()

    # refresh and filter buttons
    refresh_col, filter_col, errors_warnings_col, fake_col = st.columns([1, 1, 1, 3])
    with refresh_col:
        refresh_button = st.button("🔄️ Refresh", key="refresh", use_container_width=True)
        if refresh_button:
            stu.refresh_table_propositions("Refresh")
    with filter_col:
        filter_label_num_active_filters = stu.get_num_active_filters(as_str=True)
        with st.popover(f"🔍 {filter_label_num_active_filters}Filters:", use_container_width=True):
            st.toggle(
                "Joined by me",
                key="joined_by_me",
                value=False,
                on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering joined_by_me"},
                disabled=not st.session_state['username']
            )
            st.toggle(
                "Proposed by me",
                key="proposed_by_me",
                value=False,
                on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering proposed_by_me"},
                disabled=not st.session_state['username']
            )
            location_options = {'default': stu.get_default_location()['alias'], 'row': stu.get_rest_of_the_world_page_name()}
            location_filter_disabled = st.session_state.location_mode is not None
            st.pills(
                "Locations",
                options=location_options.keys(),
                default=st.session_state.location_mode,
                format_func=lambda x: location_options[x],
                key="location_mode_filter",
                disabled=location_filter_disabled,
                help="You can't use this filter in this page" if location_filter_disabled else "Select a location to filter tables by location.",
                on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering Location"}
            )
            proposition_options = stu.get_table_proposition_types(as_reversed_dict=True)
            proposition_filter_disabled = st.session_state.proposition_type_id_mode is not None
            st.pills(
                "Proposition Types",
                options=proposition_options.keys(),
                default=st.session_state.proposition_type_id_mode,
                format_func=lambda x: proposition_options[x],
                key="proposition_type_id_mode_filter",
                disabled=st.session_state.proposition_type_id_mode is not None,
                help="You can't use this filter in this page" if proposition_filter_disabled else "Select a proposition type to filter tables by type.",
                on_change=stu.refresh_table_propositions, kwargs={"reason": "Filtering Proposition Type"}
            )
    with errors_warnings_col:
        errors, warnings = stu.check_overlaps_in_joined_tables(st.session_state.global_propositions, st.session_state.user.user_id)
        num_overlaps = len(errors) + len(warnings)
        if num_overlaps == 0:
            with st.popover("✅ No overlaps", use_container_width=True):
                st.write("No overlaps found")
        else:
            with st.popover(f"{':exclamation:' if len(errors) else ':warning:'} {num_overlaps} overlaps", use_container_width=True):
                if len(errors):
                    st.write(f":exclamation: {len(errors)} important:")
                    for error_left, error_right in errors:
                        st.write(f"Table **\"{error_left.game_name}\"** (ID {error_left.table_id}) :red[has the same start date] "
                                 f"time as **\"{error_right.game_name}\"** (ID {error_right.table_id})")
                        stu.render_overlaps_table_buttons(error_left, error_right, "err")
                if len(warnings):
                    st.write(f":warning: {len(warnings)} warnings:")
                    for warning_left, warning_right in warnings:
                        st.write(f"Table **\"{warning_left.game_name}\"** (ID {warning_left.table_id}) :orange[has a partial "
                                 f"overlap] with **\"{warning_right.game_name}\"** (ID {warning_right.table_id})")
                        stu.render_overlaps_table_buttons(warning_left, warning_right, "warn")

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

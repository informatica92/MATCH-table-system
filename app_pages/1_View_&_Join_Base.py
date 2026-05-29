import streamlit as st

import datetime

import utils.streamlit_utils as stu
from utils.bgg_manager import get_bgg_url
from utils.altair_manager import timeline_chart
from utils.table_system_proposition import TableProposition, TablePropositionExpansion, StreamlitTablePropositions
from utils.table_system_overlaps import check_overlaps_in_joined_tables, render_overlaps_table_buttons
from utils.table_system_location import get_default_location
from utils.recommender import recommend_score


@st.dialog("🖋️ Edit Table")
def dialog_edit_table_proposition(old_table_proposition: TableProposition):
    with st.form(key=f"form-edit-{old_table_proposition.table_id}"):
        with st.container(gap=stu.SPACE_BETWEEN_VERTICAL_COMPONENTS):
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
            propositions_types = stu.get_table_proposition_types(as_list_of_dicts=True)
            # in case the old proposition type is not in the list, we set it to 0 (default => Proposition) that is always present
            index = old_table_proposition.proposition_type_id if old_table_proposition.proposition_type_id in [pt['id'] for pt in propositions_types] else 0
            if st.session_state.user.is_admin:
                st.selectbox("Proposition Type", options=propositions_types, key="proposition_type_edit", format_func=lambda x: x["value"], index=index)
            else:
                st.session_state['proposition_type_edit'] = propositions_types[index]

            submitted = st.form_submit_button("💾 Update", width="stretch")
            if submitted:
                stu.update_table_propositions(
                    old_table_proposition,
                    game_name,
                    max_players,
                    date,
                    time,
                    duration,
                    notes,
                    bgg_game_id,
                    st.session_state.location_edit[0] if st.session_state.location_edit else None,
                    st.session_state.expansions_edit,
                    st.session_state.proposition_type_edit['id']
                )
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

def display_table_proposition(section_name, table_proposition: TableProposition):
    # Check if the BGG game ID is valid and set the BGG URL
    if table_proposition.bgg_game_id and int(table_proposition.bgg_game_id) >= 1:
        bgg_url = get_bgg_url(table_proposition.bgg_game_id)
        st.subheader(f"Table {table_proposition.table_id}: [{table_proposition.game_name}]({bgg_url})", anchor=f"table-{table_proposition.table_id}")
    else:
        st.subheader(f"Table {table_proposition.table_id}: {table_proposition.game_name}", anchor=f"table-{table_proposition.table_id}")

    # Create three columns
    col1, col2, col3 = st.columns([2, 3, 3])

    with col1:  # image, description, categories, mechanics
        with st.container(horizontal=False, gap=stu.SPACE_BETWEEN_VERTICAL_COMPONENTS):
            st.image(table_proposition.image_url or stu.DEFAULT_IMAGE_URL)
            stu.st_write(table_proposition.get_description_preview(read_all_link="HTML"), color="lightgrey")
            stu.st_write(
                f"<b>Categories:</b> {', '.join(table_proposition.categories)}<br>"
                f"<b>Mechanics:</b> {', '.join(table_proposition.mechanics)}",
                color="black" if st.context.theme.get('type') == "light" else "grey"
            )

    with col2:  # time, date, duration, proposed by, location, expansions, notes
        with st.container(horizontal=False, gap=stu.SPACE_BETWEEN_VERTICAL_COMPONENTS):
            with st.container(horizontal=True):
                st.badge(f"**{table_proposition.time.strftime('%H:%M')}**", icon="⌚", color="violet")
                st.badge(f"{table_proposition.date}", icon="📅", color="blue")
                st.badge(stu.format_duration_in_h_min(table_proposition.duration, suffix="h"), icon="⏳", color="orange")
            stu.create_user_info(user=table_proposition.proposed_by, table_id=table_proposition.table_id, icon="🧔🏻", label=" **Proposed by** ")
            st.text(
                recommend_score(
                    user_categories=st.session_state.user.liked_categories,
                    user_mechanics=st.session_state.user.liked_mechanics,
                    game_categories=table_proposition.categories,
                    game_mechanics=table_proposition.mechanics,
                    cat_weight = 0.5,
                    mech_weight = 0.5,
                    beta = 1
                )
            )
            with st.expander(f"🗺️ **Location**: {table_proposition.location.location_alias}"):
                location_markdown = table_proposition.location.to_markdown(st.session_state.user, icon="🔗")
                # location_markdown includes address + link to google maps IF default location or logged users
                # otherwise it is equal to "*Unknown*"
                st.write(location_markdown)
            with st.expander(f"📦 **Expansions** ({len(table_proposition.expansions)}):"):
                expansions_markdown = TablePropositionExpansion.to_markdown_list(table_proposition.expansions)
                st.write(expansions_markdown)
            with st.expander(f"📒 **Notes**: {table_proposition.get_notes_preview()}"):
                st.write(table_proposition.notes)

    with col3:  # players joined
        with st.container(horizontal=False, gap=stu.SPACE_BETWEEN_VERTICAL_COMPONENTS):
            is_full = table_proposition.joined_count >= table_proposition.max_players
            st.write(f":{'red' if is_full else 'green'}[**Joined Players ({table_proposition.joined_count}/{table_proposition.max_players}):**]")
            for joined_player_obj in table_proposition.joined_players or []:
                if joined_player_obj.username is not None:
                    with st.container(horizontal=True, vertical_alignment="center"):  # NEW in Streamlit 1.48.0
                        stu.create_user_info(user=joined_player_obj, table_id=table_proposition.table_id)
                        # LEAVE
                        st.button(
                            "Leave",
                            key=f"leave_{table_proposition.table_id}_{joined_player_obj.username}_{section_name}",
                            on_click=stu.leave_callback, args=[table_proposition.table_id, joined_player_obj.username, joined_player_obj.user_id],
                            disabled=not stu.can_current_user_leave(joined_player_obj.username, table_proposition.proposed_by.username),
                            help="Only the table owner or the player himself can leave a table.",
                            icon="⛔"
                        )

    # Create four columns for action buttons
    with st.container(horizontal=True, vertical_alignment="center"):
        # JOIN
        if not is_full:
            if st.session_state['username']:
                st.button(
                    # JOIN
                    f"✅ Join Table {table_proposition.table_id}" if not table_proposition.joined(st.session_state.user.user_id) else "✅ *Already joined*",
                    key=f"join_{table_proposition.table_id}_{section_name}",
                    width='stretch',
                    disabled=table_proposition.joined(st.session_state.user.user_id),
                    on_click=stu.join_callback, args=[table_proposition.table_id, st.session_state['username'], st.session_state.user.user_id]
                )
            else:
                if st.session_state.user.is_logged_in():
                    st.warning("Set a username to join a table.")
                else:
                    st.warning("**Log in** to join a table.")
        else:
            st.warning(f"🟧 Table {table_proposition.table_id} is full", )
        # DELETE
        if st.button(
            "⛔ Delete",
            key=f"delete_{table_proposition.table_id}_{section_name}",
            width='stretch',
            disabled=not stu.can_current_user_delete_and_edit(table_proposition.proposed_by.username),
            help="Only the table owner can delete their tables."
        ):
            dialog_delete_table_proposition(table_proposition)
        # EDIT
        if st.button(
            "🖋️ Edit",
            key=f"edit_{table_proposition.table_id}_{section_name}",
            width='stretch',
            disabled=not stu.can_current_user_delete_and_edit(table_proposition.proposed_by.username),
            help="Only the table owner can edit their tables."
        ):
            dialog_edit_table_proposition(table_proposition)
        # FAKE SPACE ON THE RIGHT
        st.space("stretch")

def view_table_propositions():
    for proposition in st.session_state.propositions:
        proposition: TableProposition
        display_table_proposition(section_name="list", table_proposition=proposition)

def timeline_table_propositions():
    df = st.session_state.propositions.to_df(
        username=st.session_state.user.username,
        add_group=True, add_status=True, add_start_and_end_date=True
    )

    chart = timeline_chart(df)
    selected_data = st.altair_chart(chart, width='stretch', on_select="rerun", theme=None)

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("param_1", {}) and len(selected_data["selection"]["param_1"]) != 0:
            _id = selected_data["selection"]["param_1"][0]['table_id']
            selected_row = df[df['table_id'] == _id].iloc[0]
            display_table_proposition(section_name="timeline", table_proposition=TableProposition.from_dict(selected_row))

def dataframe_table_propositions():

    df = st.session_state.propositions.to_df(
        username=st.session_state.user.username,
        add_bgg_url=True, add_players_fraction=True, add_joined=True
    )

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
    selected_data = st.dataframe(df, hide_index=True, width='stretch', column_config=column_config, column_order=columns_order, on_select="rerun", selection_mode="single-row", row_height=50)

    st.subheader("Selected item")

    if selected_data:
        if selected_data.get("selection", {}).get("rows", {}) and len(selected_data["selection"]["rows"]) != 0:
            _id = selected_data["selection"]["rows"][0]
            selected_row = df.iloc[_id]
            display_table_proposition(section_name="timeline", table_proposition=TableProposition.from_dict(selected_row))

def create_view_and_join_page():

    # redirect to "User" page if username is not set
    stu.redirect_to_user_page_if_username_not_set()

    # title and help button
    stu.add_title_text(st, frmt="{title}")

    # print(f"Location mode [View Page]: {st.session_state.location_mode}")

    # additional sidebar widgets
    with st.sidebar:
        with st.container(border=True):
            st.selectbox("View mode", options=["📜List", "📊Timeline", "◻️Table"], key="view_mode")
        stu.add_donation_button()

    # refresh and filter buttons
    with st.container(horizontal=True):
        # REFRESH
        refresh_button = st.button("🔄️ Refresh", key="refresh", width='stretch')
        if refresh_button:
            StreamlitTablePropositions.refresh_table_propositions("Refresh")
        # FILTERS
        filter_label_num_active_filters = stu.get_num_active_filters(as_str=True)
        with st.popover(f"🔍 {filter_label_num_active_filters}Filters:", width='stretch'):
            st.toggle(
                "Joined by me",
                key="joined_by_me",
                value=False,
                on_change=StreamlitTablePropositions.refresh_table_propositions, kwargs={"reason": "Filtering joined_by_me"},
                disabled=not st.session_state['username']
            )
            st.toggle(
                "Proposed by me",
                key="proposed_by_me",
                value=False,
                on_change=StreamlitTablePropositions.refresh_table_propositions, kwargs={"reason": "Filtering proposed_by_me"},
                disabled=not st.session_state['username']
            )
            location_options = {'default': get_default_location()['alias'], 'row': stu.get_rest_of_the_world_page_name()}
            location_filter_disabled = st.session_state.location_mode is not None
            st.pills(
                "Locations",
                options=location_options.keys(),
                default=st.session_state.location_mode,
                format_func=lambda x: location_options[x],
                key="location_mode_filter",
                disabled=location_filter_disabled,
                help="You can't use this filter in this page" if location_filter_disabled else "Select a location to filter tables by location.",
                on_change=StreamlitTablePropositions.refresh_table_propositions, kwargs={"reason": "Filtering Location"}
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
                on_change=StreamlitTablePropositions.refresh_table_propositions, kwargs={"reason": "Filtering Proposition Type"}
            )
        # OVERLAPS
        errors, warnings = check_overlaps_in_joined_tables(st.session_state.global_propositions)
        num_overlaps = len(errors) + len(warnings)
        if num_overlaps == 0:
            with st.popover("✅ No overlaps", width='stretch'):
                st.write("No overlaps found")
        else:
            with st.popover(f"{':exclamation:' if len(errors) else ':warning:'} {num_overlaps} overlaps", width='stretch'):
                if len(errors):
                    st.write(f":exclamation: {len(errors)} important:")
                    for error_left, error_right in errors:
                        st.write(f"Table **\"{error_left.game_name}\"** (ID {error_left.table_id}) :red[has the same start date] "
                                 f"time as **\"{error_right.game_name}\"** (ID {error_right.table_id})")
                        render_overlaps_table_buttons(error_left, error_right, "err")
                if len(warnings):
                    st.write(f":warning: {len(warnings)} warnings:")
                    for warning_left, warning_right in warnings:
                        st.write(f"Table **\"{warning_left.game_name}\"** (ID {warning_left.table_id}) :orange[has a partial "
                                 f"overlap] with **\"{warning_right.game_name}\"** (ID {warning_right.table_id})")
                        render_overlaps_table_buttons(warning_left, warning_right, "warn")
        # FAKE SPACE ON THE RIGHT
        st.space("stretch")

    # statistics with st.metrics
    with st.container(horizontal=True, gap="xxsmall"):
        st.metric("Tables", f"{len(st.session_state.propositions)} :material/table_restaurant:", border=False, help="The total number of tables available.")
        st.metric("Joined", f"{len(st.session_state.propositions.get_joined_tables())} :material/how_to_reg:", border=False, help="The number of tables joined by the current user.")
        st.metric("Play Time", f"{stu.format_duration_in_h_min(st.session_state.propositions.get_booked_play_time())}h", border=False, help="The total expected play time booked by the joined tables of the current user.")
        st.metric("Proposed", f"{len(st.session_state.propositions.get_proposed_tables())} :material/add_box:", border=False, help="The total number of tables proposed by the current user.")

    # show propositions
    if len(st.session_state.propositions) == 0:
        st.info("No table propositions available, use the \"**➕Create**\" page to create a new one."
                "\n\n*NB: tables are automatically hidden after 1 day*")
    else:
        if st.session_state['view_mode'] == "📜List":
            view_table_propositions()
        elif st.session_state['view_mode'] == "📊Timeline":
            timeline_table_propositions()
        else:
            dataframe_table_propositions()

    st.divider()
    stu.add_powered_by_bgg_image()

    if st.session_state.get("last_created_table_id"):
        navigate_to_table_id = st.session_state.last_created_table_id
        stu.scroll_to(f"table-{navigate_to_table_id}")
        st.session_state.last_created_table_id = None
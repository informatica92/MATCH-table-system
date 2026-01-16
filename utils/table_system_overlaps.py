import streamlit as st
from utils.streamlit_utils import scroll_to, VIEW_JOIN_PROPOSITIONS_PAGE, VIEW_JOIN_TOURNAMENTS_PAGE, VIEW_JOIN_DEMOS_PAGE
from utils.table_system_proposition import TableProposition

def check_overlaps_in_joined_tables(
        table_propositions:  list[TableProposition],
        current_user_id: int
) -> tuple[list[tuple[TableProposition, TableProposition]], list[tuple[TableProposition, TableProposition]]]:
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
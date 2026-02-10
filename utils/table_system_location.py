import streamlit as st
import pandas as pd
from utils.sql_manager import SQLManager
from utils.table_system_proposition import StreamlitTablePropositions


sql_manager = SQLManager()

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

    StreamlitTablePropositions.refresh_table_propositions("Location Update")

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

def display_system_locations(default_location_page_name=None, non_default_location_page_name=None):
    system_locations = get_available_locations(None, True, True)
    system_locations["address"] = system_locations[['street_name', 'house_number', 'city']].agg(', '.join, axis=1)
    system_locations['pages'] = system_locations['is_default'].map(
        {
            True:  [f"📜{default_location_page_name}"],
            False: [f"🌍{non_default_location_page_name}"]
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
    if not location_id:
        return True
    if isinstance(location_id, tuple) or isinstance(location_id, list):
        location_id = location_id[0]
    return int(location_id) == int(get_default_location()["id"])
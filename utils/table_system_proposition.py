import datetime
import time as time_module
import pandas as pd
from utils.bgg_manager import get_bgg_game_info, get_bgg_url
from utils.table_system_user import StreamlitTableSystemUser
from utils.table_system_logging import logging
from utils.sql_manager import SQLManager
import streamlit as st

# create a function that accepts an object in input and a number of chars for its preview, check if it is a string, if
# not returns it as it is, otherwise checks the sting len, if it is smaller than the number of chars for the preview,
# return it as it is, otherwise return the first n chars and append the '...' to highlight the truncation

def _str_preview(obj: str, n_chars: int):
    # if obj is not a string...
    if not isinstance(obj, str):
        return obj
    # if it is a string...
    if len(obj) <= n_chars:
        return obj
    else:
        return obj[:n_chars] + '...'

class TablePropositionExpansion(object):
    def __init__(
            self,
            expansion_id: int,
            expansion_name: str
    ):
        self.expansion_id = expansion_id
        self.expansion_name = expansion_name

    def to_dict(self) -> dict:
        return {
            'id': self.expansion_id,
            'value': self.expansion_name
        }

    @staticmethod
    def from_dict(dict_) -> 'TablePropositionExpansion':
        return TablePropositionExpansion(
            expansion_id=dict_['id'],
            expansion_name=dict_['value']
        )

    @staticmethod
    def from_list_of_dicts(list_) -> list['TablePropositionExpansion']:
        return [TablePropositionExpansion.from_dict(expansion) for expansion in list_]

    @staticmethod
    def to_list_of_dicts(list_) -> list[dict]:
        return [expansion.to_dict() for expansion in list_]

    def to_markdown(self) -> str:
        """
        Format the expansion as a Markdown link.
        :return: Markdown formatted string for the expansion.
        """
        return f"[{self.expansion_name}]({get_bgg_url(self.expansion_id)})"

    @staticmethod
    def to_markdown_list(expansions: list['TablePropositionExpansion']) -> str:
        return ', '.join(
            [f"\n - {expansion.to_markdown()}" for expansion in expansions]
        )


class JoinedPlayerOrProposer(object):
    def __init__(
            self,
            user_id: int,
            username: str,
            email: str = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email

    @staticmethod
    def from_dict(dict_) -> 'JoinedPlayerOrProposer':
        return JoinedPlayerOrProposer(
            user_id=dict_['user_id'],
            username=dict_['username'],
            email=dict_['email']
        )

    @staticmethod
    def from_list_of_dicts(list_) -> list['JoinedPlayerOrProposer']:
        return [JoinedPlayerOrProposer.from_dict(player) for player in list_]

    @staticmethod
    def from_tuples(id_tuple, username_tuples, email_tuples) -> list['JoinedPlayerOrProposer']:
        return [JoinedPlayerOrProposer(user_id, username, email) for user_id, username, email in zip(id_tuple, username_tuples, email_tuples) if username]


class TablePropositionLocation(object):
    def __init__(
            self,
            location_alias: str,
            location_address: str,
            location_is_system: bool,
            location_is_default: bool
    ):
        self.location_alias = location_alias
        self.location_address = location_address
        self.location_is_system = location_is_system
        self.location_is_default = location_is_default

    @staticmethod
    def from_dict(dict_) -> 'TablePropositionLocation':
        return TablePropositionLocation(
            location_alias=dict_['location_alias'],
            location_address=dict_['location_address'],
            location_is_system=dict_['location_is_system'],
            location_is_default=dict_.get('location_is_default')
        )

    def to_markdown(self, user: StreamlitTableSystemUser, icon="🗺️"):
        if user.is_logged_in() or self.location_is_system:
            if self.location_alias:
                location_md = f"{self.location_address}\n\n"
                location_md += f"{icon} [{self.location_alias}](https://maps.google.com/?q={self.location_address.replace(' ', '+')})"
            else:
                location_md = "*Unknown*"
        else:
            location_md = "*Login to see the location*"
        return location_md

class TableProposition(object):
    def __init__(
            self,
            table_id: int,
            game_name: str,
            max_players: int,
            date: datetime.date,
            time: datetime.time,
            duration: int,
            notes: str,
            bgg_game_id: int,
            proposed_by_id: int,
            proposed_by_username: str,
            proposed_by_email: str,
            joined_players: list[str],
            joined_players_emails: list[str],
            joined_players_ids: list[int],
            location_alias: str,
            location_address: str,
            location_is_system: bool,
            location_is_default: bool,
            expansions: list[dict],
            proposition_type_id: int,
            **kwargs
    ):
        self.table_id: int = table_id
        self.game_name: str = game_name
        self.bgg_game_id: int = bgg_game_id
        self.proposed_by: JoinedPlayerOrProposer = JoinedPlayerOrProposer(proposed_by_id, proposed_by_username, proposed_by_email)
        self.max_players: int = max_players
        self.date: datetime.date = date
        self.time: datetime.time = time
        self.duration: int = duration
        self.notes: str = notes
        self.joined_players: list[JoinedPlayerOrProposer] = JoinedPlayerOrProposer.from_tuples(joined_players_ids, joined_players, joined_players_emails)
        self.location: TablePropositionLocation = TablePropositionLocation(location_alias, location_address, location_is_system, location_is_default)
        self.expansions: list[TablePropositionExpansion] = TablePropositionExpansion.from_list_of_dicts(expansions)
        self.proposition_type_id: int = proposition_type_id or 0
        # BGG info:
        image_url, game_description, categories, mechanics, available_expansions, _ = get_bgg_game_info(bgg_game_id)
        self.image_url = image_url
        self.game_description = game_description
        self.categories = categories
        self.mechanics = mechanics
        self.available_expansions = TablePropositionExpansion.from_list_of_dicts(available_expansions)

    def to_dict(self, simple=False) -> dict:
        if simple:
            return {
                'table_id': self.table_id,
                'game_name': self.game_name,
                'bgg_game_id': self.bgg_game_id,
                'proposed_by_id': self.proposed_by.user_id,
                'proposed_by_username': self.proposed_by.username,
                'proposed_by_email': self.proposed_by.email,
                'max_players': self.max_players,
                'date': self.date,
                'time': self.time,
                'duration': self.duration,
                'notes': self.notes,
                'joined_players': self.get_joined_players_usernames(),
                'joined_players_emails': [player.email for player in self.joined_players],
                'joined_players_ids': [player.user_id for player in self.joined_players],
                'joined_count': self.joined_count,
                'location_alias': self.location.location_alias,
                'location_address': self.location.location_address,
                'location_is_system': self.location.location_is_system,
                'location_is_default': self.location.location_is_default,
                'expansions': [expansion.to_dict() for expansion in self.expansions],
                'proposition_type_id': self.proposition_type_id,
                'image_url': self.image_url,
            }
        else:
            return {
                'table_id': self.table_id,
                'game_name': self.game_name,
                'bgg_game_id': self.bgg_game_id,
                'proposed_by': {
                    'user_id': self.proposed_by.user_id,
                    'username': self.proposed_by.username,
                    'email': self.proposed_by.email
                },
                'max_players': self.max_players,
                'date': self.date,
                'time': self.time,
                'duration': self.duration,
                'notes': self.notes,
                'joined_players': [
                    {
                        'user_id': player.user_id,
                        'username': player.username,
                        'email': player.email
                    } for player in self.joined_players
                ],
                'joined_count': self.joined_count,
                'location': {
                    'location_alias': self.location.location_alias,
                    'location_address': self.location.location_address,
                    'location_is_system': self.location.location_is_system,
                    'location_is_default': self.location.location_is_default
                },
                'expansions': [
                    {
                        'id': expansion.expansion_id,
                        'value': expansion.expansion_name
                    } for expansion in self.expansions
                ],
                'proposition_type_id': self.proposition_type_id,
                'image_url': self.image_url,
            }

    def get_joined_players_usernames(self):
        return [player.username for player in self.joined_players]

    def joined(self, user_id: int) -> bool:
        """
        Check if a user is already joined to this table proposition.
        :param user_id: The ID of the user to check.
        :return: True if the user is joined, False otherwise.
        """
        return any(player.user_id == user_id for player in self.joined_players)

    def get_notes_preview(self, n_chars=20):
        return _str_preview(self.notes, n_chars)

    def get_description_preview(self, n_chars=120):
        return _str_preview(self.game_description, n_chars)

    # PROPERTIES

    @property
    def joined_count(self):
        return len(self.joined_players)

    @property
    def start_datetime(self):
        return datetime.datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M:%S")

    @property
    def end_datetime(self):
        return self.start_datetime + datetime.timedelta(minutes=self.duration)

    # STATIC METHODS
    # # FROMs

    @staticmethod
    def from_dict(dict_) -> 'TableProposition':
        return TableProposition(**dict_)

    @staticmethod
    def from_tuple(tuple_) -> 'TableProposition':
        """
        elements in tuple must be in the following order:
         - table_id,
         - game_name,
         - bgg_game_id,
         - proposed_by,
         - max_players,
         - date,
         - time,
         - duration,
         - notes,
         - joined_players,
         - joined_players_ids,
         - location_alias,
         - location_address,
         - location_is_system,
         - location_is_default,
         - expansions
         - proposition_type_id
        :param tuple_:
        :return:
        """
        return TableProposition(*tuple_)


class StreamlitTablePropositions(list[TableProposition]):
    """A list-like container for TableProposition with helpers for creation, conversion and DataFrame export."""

    @staticmethod
    def refresh_table_propositions(reason, **kwargs):
        """
        Refresh the table propositions in the session state
        :param reason: the reason why the refresh is needed (Init, Delete, Join...)
        :param kwargs: contextual information for the given reason (Delete: the deleted table id, Create: game name, table id...)
        :return:
        """
        query_start_time = time_module.time()

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
        proposition_type_id_mode = st.session_state.get("proposition_type_id_mode") if st.session_state.get(
            "proposition_type_id_mode") is not None else st.session_state.get("proposition_type_id_mode_filter")

        st.session_state.global_propositions = StreamlitTablePropositions.from_list_of_tuples(SQLManager().get_table_propositions())
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
            st.session_state.propositions = [tp for tp in st.session_state.propositions if
                                             tp.proposition_type_id == proposition_type_id_mode]

        logging.info(f"[User: {st.session_state.user if st.session_state.get('user') else '(not instantiated)'}] "
                     f"Table propositions QUERY [{reason}] refreshed in {(time_module.time() - query_start_time):.4f}s "
                     f"({len(st.session_state.propositions)} rows) "
                     f"(context: {kwargs})")

    # Construction helpers
    @classmethod
    def from_list_of_tuples(cls, list_of_tuples: list[tuple]) -> "StreamlitTablePropositions":
        return cls([TableProposition.from_tuple(t) for t in list_of_tuples])

    def add_from_dict(self, dict_: dict) -> None:
        """Create a TableProposition from a dict and append it."""
        self.append(TableProposition.from_dict(dict_))

    def add_from_tuple(self, tuple_: tuple) -> None:
        """Create a TableProposition from a tuple and append it."""
        self.append(TableProposition.from_tuple(tuple_))

    def append_proposition(self, proposition: TableProposition) -> None:
        """Append an existing TableProposition instance (type-checked)."""
        if not isinstance(proposition, TableProposition):
            raise TypeError("proposition must be a TableProposition")
        self.append(proposition)

    def extend_from_dicts(self, list_of_dicts: list[dict]) -> None:
        """Extend the list by creating TableProposition objects from a list of dicts."""
        for d in list_of_dicts:
            self.add_from_dict(d)

    # Conversion helpers
    def to_list_of_dicts(self, simple: bool = False) -> list[dict]:
        """Return list of dict representations for contained TableProposition objects."""
        return [p.to_dict(simple=simple) for p in self]

    # DataFrame export (moved from TableProposition.table_propositions_to_df)
    def to_df(
        self,
        username: str = None,
        add_start_and_end_date: bool = False,
        add_group: bool = False,
        add_status: bool = False,
        add_bgg_url: bool = False,
        add_players_fraction: bool = False,
        add_joined: bool = False,
    ):
        df = pd.DataFrame(self.to_list_of_dicts(simple=True))

        if add_start_and_end_date:
            df['start_datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
            df['end_datetime'] = df['start_datetime'] + pd.to_timedelta(df['duration'], unit='minute')

        if add_group:
            df['group'] = df['time'].apply(
                lambda x: 'Morning' if x.hour < 12 else 'Afternoon' if x.hour < 18 else 'Evening')

        if add_status:
            df['status'] = df.apply(lambda x: 'Full' if x['joined_count'] == x['max_players'] else 'Available', axis=1)

        if add_bgg_url:
            df['bgg'] = df['bgg_game_id'].apply(get_bgg_url)

        if add_players_fraction:
            df['players'] = df['joined_count'].astype(str) + "/" + df['max_players'].astype(str)

        if add_joined:
            if username:
                df['joined'] = df['joined_players'].apply(
                    lambda x: username.lower() in [player.lower() for player in x])
            else:
                df['joined'] = False

        return df.sort_values(["date", "time"])


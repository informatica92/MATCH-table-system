import datetime
import time as time_module
from utils.bgg_manager import get_bgg_game_info, get_bgg_url
from utils.table_system_user import StreamlitTableSystemUser

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
            time: time_module.time,
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
        self.time: time_module.time = time
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
    # # FROMS

    @staticmethod
    def from_dict(dict_) -> 'TableProposition':
        return TableProposition(**dict_)

    @staticmethod
    def from_list_of_tuples(list_: list[tuple]) -> list['TableProposition']:
        return [TableProposition.from_tuple(proposition) for proposition in list_]

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

    # # TOS
    @staticmethod
    def to_list_of_dicts(list_: list['TableProposition'], simple=False) -> list[dict]:
        return [proposition.to_dict(simple=simple) for proposition in list_]


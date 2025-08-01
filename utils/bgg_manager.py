import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import html
import xml.etree.ElementTree as et

from streamlit import cache_data

from utils.table_system_logging import logging


@cache_data(ttl=None, max_entries=1000, persist="disk")
def get_bgg_game_info(game_id):
    logging.info(f"\tquerying BGG for {game_id}")
    # BGG API URL for game details
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"

    # --- Create a session with retries ---
    session = requests.Session()

    retries = Retry(
        total=5,  # Total number of retries
        backoff_factor=1,  # Wait time between retries (exponential backoff)
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["GET"],  # Only retry on GET requests
        raise_on_status=False  # Do not raise on status; we'll handle it
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        # Make a GET request to fetch the game data
        response = session.get(url)

        # Raise an HTTPError for bad responses
        response.raise_for_status()

        # Parse the XML response
        root = et.fromstring(response.content)

        # Find the game name
        game_name = root.find('item/name[@type="primary"]').get('value')

        # Find the game year published
        year = root.find('item/yearpublished')

        game_name_with_year = f"{game_name} ({year.get('value')})" if year is not None else game_name

        # Find the image tag and extract the URL
        image_url = root.find('item/image').text if root.find('item/image') is not None else None

        game_description = root.find('item/description').text or ""
        game_description = html.unescape(game_description)
        game_description = '\n'.join([s.strip() for s in game_description.splitlines()])

        categories = []
        for category in root.findall('item/link[@type="boardgamecategory"]'):
            categories.append(category.get('value'))

        mechanics = []
        for mechanic in root.findall('item/link[@type="boardgamemechanic"]'):
            mechanics.append(mechanic.get('value'))

        expansions = []
        for expansion in root.findall('item/link[@type="boardgameexpansion"]'):
            expansions.append({'id': expansion.get('id'), 'value': expansion.get('value')})

        return image_url, game_description, categories, mechanics, expansions, game_name_with_year
    except Exception as e:
        logging.error(f"Error fetching game image: {e}")
        return None, "", [], [], [], ""


def get_bgg_url(game_id):
    return f"https://boardgamegeek.com/boardgame/{game_id}"

def get_bgg_profile_page_url(username, as_html_link=False):
    url = f"https://boardgamegeek.com/user/{username}"
    if as_html_link:
        return f"<a href='{url}' target='_blank'>{url}</a>"
    else:
        return url


def search_bgg_games(game_name):
    url = f"https://boardgamegeek.com/xmlapi2/search?query={game_name}&type=boardgame"
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = et.fromstring(response.content)

        games = []
        for item in root.findall('item'):
            game_id = item.get('id')
            name = item.find('name').get('value')
            year = item.find('yearpublished')
            year = year.get('value') if year is not None else "Unknown Year"
            games.append((game_id, f"{name} ({year})"))

        return games
    except Exception as e:
        raise AttributeError(e)

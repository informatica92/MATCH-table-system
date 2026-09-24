import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import html
import xml.etree.ElementTree as et

from streamlit import cache_data

from utils.table_system_logging import logging

BGG_API_BEARER_TOKEN = os.getenv("BGG_API_BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BGG_API_BEARER_TOKEN}"}


class BGGCollectionQueuedError(Exception):
    """Raised when BGG keeps returning HTTP 202 (collection request still being processed)."""
    pass


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
        response = session.get(url, headers=HEADERS)

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

def get_bgg_profile_page_url(username, as_html_link=False, label=None):
    url = f"https://boardgamegeek.com/user/{username}"
    if not label:
        label = url
    if as_html_link:
        return f"<a href='{url}' target='_blank'>{label}</a>"
    else:
        return url


def search_bgg_games(game_name):
    url = f"https://boardgamegeek.com/xmlapi2/search?query={game_name}&type=boardgame"
    try:
        response = requests.get(url, headers=HEADERS)
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


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_bgg_owned_games(username, queue_retries=5, queue_wait_seconds=5):
    """Fetch the games a BGG user marks as *owned* via the BGG XML API2 collection endpoint.

    The collection endpoint is asynchronous: BGG may answer HTTP 202 ("your request has been queued")
    and only return the data on a subsequent call. We poll up to ``queue_retries`` times, waiting
    ``queue_wait_seconds`` between attempts. Note: this waiting is on top of the caller-side 1/min
    rate limiting enforced by the background sync job (see utils/bgg_collection_sync.py).

    Returns a list of dicts, one per owned game, with keys: bgg_game_id, name, year_published,
    image_url, thumbnail_url, min_players, max_players, playing_time, num_plays, average_rating.

    Raises BGGCollectionQueuedError if BGG never stops returning 202, or AttributeError on other errors.
    """
    url = f"https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1&stats=1"

    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    response = None
    for attempt in range(queue_retries):
        response = session.get(url, headers=HEADERS)
        if response.status_code == 202:
            # Request accepted but not ready yet: wait and retry.
            logging.info(f"\tBGG collection for '{username}' queued (202), retry {attempt + 1}/{queue_retries}")
            time.sleep(queue_wait_seconds)
            continue
        break

    if response is None or response.status_code == 202:
        raise BGGCollectionQueuedError(
            f"BGG collection for '{username}' still queued after {queue_retries} retries"
        )

    try:
        response.raise_for_status()
        root = et.fromstring(response.content)
    except Exception as e:
        raise AttributeError(e)

    games = []
    for item in root.findall('item'):
        bgg_game_id = _to_int(item.get('objectid'))
        if bgg_game_id is None:
            continue

        name_el = item.find('name')
        name = name_el.text if name_el is not None else None

        year_el = item.find('yearpublished')
        year_published = _to_int(year_el.text) if year_el is not None else None

        image_el = item.find('image')
        image_url = image_el.text if image_el is not None else None

        thumbnail_el = item.find('thumbnail')
        thumbnail_url = thumbnail_el.text if thumbnail_el is not None else None

        numplays_el = item.find('numplays')
        num_plays = _to_int(numplays_el.text) if numplays_el is not None else None

        min_players = max_players = playing_time = average_rating = None
        stats_el = item.find('stats')
        if stats_el is not None:
            min_players = _to_int(stats_el.get('minplayers'))
            max_players = _to_int(stats_el.get('maxplayers'))
            playing_time = _to_int(stats_el.get('playingtime'))
            average_el = stats_el.find('rating/average')
            if average_el is not None:
                average_rating = _to_float(average_el.get('value'))

        games.append({
            'bgg_game_id': bgg_game_id,
            'name': name,
            'year_published': year_published,
            'image_url': image_url,
            'thumbnail_url': thumbnail_url,
            'min_players': min_players,
            'max_players': max_players,
            'playing_time': playing_time,
            'num_plays': num_plays,
            'average_rating': average_rating,
        })

    return games

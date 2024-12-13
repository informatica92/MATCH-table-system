import requests
import html
import xml.etree.ElementTree as et
from cachetools import cached, LRUCache


@cached(cache=LRUCache(maxsize=128))
def get_bgg_game_info(game_id):
    print(f"\tquerying BGG for {game_id}")
    # BGG API URL for game details
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"

    try:
        # Make a GET request to fetch the game data
        response = requests.get(url)

        # Raise an HTTPError for bad responses
        response.raise_for_status()

        # Parse the XML response
        root = et.fromstring(response.content)

        # Find the image tag and extract the URL
        image_url = root.find('item/image').text

        game_description = root.find('item/description').text

        categories = []
        for category in root.findall('item/link[@type="boardgamecategory"]'):
            categories.append(category.get('value'))

        mechanics = []
        for mechanic in root.findall('item/link[@type="boardgamemechanic"]'):
            mechanics.append(mechanic.get('value'))

        return image_url, html.unescape(game_description), categories, mechanics
    except Exception as e:
        print(f"Error fetching game image: {e}")
        return None


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

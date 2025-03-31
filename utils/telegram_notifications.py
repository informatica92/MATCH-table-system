import telegram
import os
import asyncio
import requests
from io import BytesIO
from PIL import Image

from utils.table_system_logging import logging


TEXTS = {
    'IT': {
        'new_table_simple': "*{proposed_by}* ha appena creato un tavolo di *{game_name}* per {max_players} giocatori "
                            "il {date} alle *{time}* ({duration} ore) - (id: {table_id})."
                            "\n\nDai un'occhiata qui: https://match-table-system.streamlit.app/",
        'new_table': "*{proposed_by}* ha appena proposto un nuovo tavolo (id: {table_id}):"
                     "\n - 🀄 *{game_name}* "
                     "\n - 👤 {max_players} giocatori "
                     "\n - 📅 {date} alle *{time}* "
                     "\n - ⌛ {duration} ore"
                     "\n - 🗺️ presso *{location_alias}*."
                     "\n\n🔗 Dai un'occhiata qui:\n{base_url}/{row_page}#table-{table_id}"
    }
}


def get_telegram_profile_page_url(telegram_username, as_html_link=False):
    url = f"https://t.me/{telegram_username}"
    if as_html_link:
        return f"<a href='{url}'>{url}</a>"
    else:
        return url


def resize_image_from_url(image_url) -> BytesIO:
    # Download the image
    response = requests.get(image_url)
    response.raise_for_status()

    # Load image into memory
    image = Image.open(BytesIO(response.content))

    # Compute new width while maintaining aspect ratio
    width, height = image.size
    new_height = 1000 if height > 1000 else height
    new_width = int((new_height / height) * width)

    # Resize the image
    image = image.resize((new_width, new_height), Image.Resampling.NEAREST)

    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    return image_bytes  # Returns a PIL Image object

class TelegramNotifications(object):
    def __init__(self, bot_token=None, chat_id=None, language='IT'):
        self._default_chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
        self.chat_id_map = {
            (0, True): os.environ.get('TELEGRAM_CHAT_ID_PROPOSITION_DEFAULT'),
            (0, False): os.environ.get('TELEGRAM_CHAT_ID_PROPOSITION_ROW'),
            (1, True): os.environ.get('TELEGRAM_CHAT_ID_TOURNAMENT'),
            (1, False): os.environ.get('TELEGRAM_CHAT_ID_TOURNAMENT'),
            (2, True): os.environ.get('TELEGRAM_CHAT_ID_DEMO'),
            (2, False): os.environ.get('TELEGRAM_CHAT_ID_DEMO'),
        }

        self.language = language

        _bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')

        if not _bot_token:
            self._bot = None
            self.loop = None
        else:
            self._bot = telegram.Bot(token=_bot_token)
            self.loop = asyncio.new_event_loop()

    def _get_chat_id(self, proposition_type_id: int, is_default_location: bool) -> (str, int):
        """
        Get the chat_id and message_thread_id for the given proposition_type_id.
        :param proposition_type_id: The proposition type ID (0 = Proposition, 1 = Tournament, 2 = Demo)
        :return: chat_id, message_thread_id
        """
        chat_id = self.chat_id_map.get((proposition_type_id, is_default_location)) or self._default_chat_id
        if '_' in chat_id:
            chat_id, message_thread_id = chat_id.split('_')
            message_thread_id = int(message_thread_id)
            # if the message_thread_id is 1 the send_message returns an error, so we set it to None
            # if the message_thread_id is 0 or lower, it will be ignored and set to None
            if message_thread_id <= 1:
                message_thread_id = None
        else:
            message_thread_id = None
        return chat_id, message_thread_id

    @staticmethod
    def _get_page(proposition_type_id: int=None, is_default_location: bool=False) -> str:
        """
        Get the page name based on the proposition_type_id and is_default_location flag.
        :param proposition_type_id: The proposition type ID (0 = Proposition, 1 = Tournament, 2 = Demo)
        :param is_default_location: Whether the location is default or not
        :return: page name
        """
        # no '/' at the end of the page name
        if proposition_type_id == 0 and is_default_location:
            return ""  # homepage
        elif proposition_type_id == 0 and not is_default_location:
            return "restoftheworld"
        elif proposition_type_id == 1:
            return "tournaments"
        elif proposition_type_id == 2:
            return "demos"
        else:
            return ""

    def _send_text_message(self, text: str, chat_id: str, message_thread_id: int):
        if self._bot:
            try:
                self.loop.run_until_complete(
                    self._bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        message_thread_id=message_thread_id
                    )
                )
            except telegram.error.TelegramError as e:
                logging.error(f"Error sending Telegram TEXT message: '{e}'")
        else:
            logging.warning("Skipping Telegram notification since no bot token has been found")

    def _send_photo_message(self, text: str, chat_id: str, message_thread_id: int, image_url: str):
        if self._bot:
            image_file = resize_image_from_url(image_url)
            try:
                self.loop.run_until_complete(
                    self._bot.send_photo(
                        chat_id=chat_id,
                        photo=image_file,
                        caption=text,
                        parse_mode='Markdown',
                        message_thread_id=message_thread_id
                    )
                )
            except telegram.error.TelegramError as e:
                logging.error(f"Error sending Telegram PHOTO message with image: '{e}', retrying without image")
                self._send_text_message(text=text, chat_id=chat_id, message_thread_id=message_thread_id)
        else:
            logging.warning("Skipping Telegram notification since no bot token has been found")

    def send_message(self, text: str, chat_id: str, message_thread_id: int, image_url: str=None):
        if image_url:
            self._send_photo_message(text=text, chat_id=chat_id, message_thread_id=message_thread_id, image_url=image_url)
        else:
            self._send_text_message(text=text, chat_id=chat_id, message_thread_id=message_thread_id)

    def send_new_table_message(
            self,
            game_name: str,
            max_players: int,
            date: str,
            time: str,
            duration: int,
            proposed_by: str,
            table_id: int,
            is_default_location: bool,
            location_alias: str,
            image_url: str=None,
            proposition_type_id: int=None
    ):
        """
        Send a new table message to the Telegram chat.
        :param game_name:
        :param max_players:
        :param date:
        :param time:
        :param duration:
        :param proposed_by:
        :param table_id:
        :param is_default_location:
        :param location_alias:
        :param image_url:
        :param proposition_type_id:
        :return:
        """

        chat_id, message_thread_id = self._get_chat_id(proposition_type_id, is_default_location)
        page_name = self._get_page(proposition_type_id, is_default_location)

        text = TEXTS[self.language]['new_table'].format(
            game_name=game_name,
            max_players=max_players,
            date=date,
            time=time,
            duration=duration,
            proposed_by=proposed_by,
            table_id=table_id,
            row_page=page_name,
            base_url=os.environ.get('BASE_URL', 'http://localhost:8501'),
            location_alias=location_alias
        )

        self.send_message(text=text, image_url=image_url, chat_id=chat_id, message_thread_id=message_thread_id)
        # print(text, chat_id, message_thread_id)

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
        self.channel_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')

        self.language = language

        _bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')

        if not _bot_token:
            self._bot = None
            self.loop = None
        else:
            self._bot = telegram.Bot(token=_bot_token)
            self.loop = asyncio.new_event_loop()

    def send_new_table_message(self, game_name, max_players, date, time, duration, proposed_by, table_id, is_default_location, location_alias, image_url=None):

        text = TEXTS[self.language]['new_table'].format(
            game_name=game_name,
            max_players=max_players,
            date=date,
            time=time,
            duration=duration,
            proposed_by=proposed_by,
            table_id=table_id,
            row_page="" if is_default_location else "restoftheworld",  # no '/' at the end of the page name
            base_url=os.environ.get('BASE_URL', 'http://localhost:8501'),
            location_alias=location_alias
        )

        if self._bot:
            # asyncio.run(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
            if not image_url:
                self.loop.run_until_complete(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
            else:
                image_file = resize_image_from_url(image_url)
                try:
                    self.loop.run_until_complete(self._bot.send_photo(chat_id=self.channel_id, photo=image_file, caption=text, parse_mode='Markdown'))
                except telegram.error.TelegramError as e:
                    logging.warning(f"Warning sending Telegram message: '{e}', retrying without image")
                    self.loop.run_until_complete(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
        else:
            logging.warning("Skipping Telegram notification since no bot token has been found")

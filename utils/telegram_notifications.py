import telegram
import os
import asyncio


TEXTS = {
    'IT': {
        'new_table_simple': "*{proposed_by}* ha appena creato un tavolo di *{game_name}* per {max_players} giocatori "
                            "il {date} alle *{time}* ({duration} ore) - (id: {table_id})."
                            "\n\nDai un'occhiata qui: https://match-table-system.streamlit.app/",
        'new_table': "*{proposed_by}* ha appena proposto un nuovo tavolo (id: {table_id}):"
                     "\n - 🀄 *{game_name}* "
                     "\n - 👤 {max_players} giocatori "
                     "\n - 📅 {date} alle *{time}* "
                     "\n - ⌛ {duration} ore."
                     "\n\n🔗 Dai un'occhiata qui:\n{base_url}/{row_page}#table-{table_id}"
    }
}


def get_telegram_profile_page_url(telegram_username, as_html_link=False):
    url = f"https://t.me/{telegram_username}"
    if as_html_link:
        return f"<a href='{url}'>{url}</a>"
    else:
        return url

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

    def send_new_table_message(self, game_name, max_players, date, time, duration, proposed_by, table_id, is_default_location):

        text = TEXTS[self.language]['new_table'].format(
            game_name=game_name,
            max_players=max_players,
            date=date,
            time=time,
            duration=duration,
            proposed_by=proposed_by,
            table_id=table_id,
            row_page="" if is_default_location else "restoftheworld",  # no '/' at the end of the page name
            base_url=os.environ.get('BASE_URL', 'http://localhost:8501')
        )

        if self._bot:
            self.loop.run_until_complete(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
            #asyncio.run(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
        else:
            print("Skipping Telegram notification since no bot token has been found")

import telegram
import os
import asyncio


TEXTS = {
    'IT': {
        'new_table_simple': "*{proposed_by}* ha appena creato un tavolo di *{game_name}* per {max_players} giocatori "
                            "il {date} alle *{time}* ({duration} ore)."
                            "\n\nDai un'occhiata qui: https://match-table-system.streamlit.app/",
        'new_table': "*{proposed_by}* ha appena proposto un nuovo tavolo:"
                     "\n - 🀄 *{game_name}* "
                     "\n - 👤 {max_players} giocatori "
                     "\n - 📅 {date} alle *{time}* "
                     "\n - ⌛ {duration} ore."
                     "\n\nDai un'occhiata qui: https://match-table-system.streamlit.app/"
    }
}


class TelegramNotifications(object):
    def __init__(self, bot_token=None, chat_id=None, language='IT'):
        self.channel_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')

        self.language = language

        _bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')

        if not _bot_token:
            self._bot = None
        else:
            self._bot = telegram.Bot(token=_bot_token)

    def send_new_table_message(self, game_name, max_players, date, time, duration, proposed_by):

        text = TEXTS[self.language]['new_table'].format(
            game_name=game_name,
            max_players=max_players,
            date=date,
            time=time,
            duration=duration,
            proposed_by=proposed_by
        )

        if self._bot:
            asyncio.run(self._bot.send_message(chat_id=self.channel_id, text=text, parse_mode='Markdown', disable_web_page_preview=True))
        else:
            print("Skipping Telegram notification since no bot token has been found")

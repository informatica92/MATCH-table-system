# AGENTS: How to be productive in the MATCH Table System codebase

Purpose: give an AI coding agent the exact, repo-specific knowledge to be productive quickly — major components, runtime side-effects, example call sites and recipes for adding or changing "agents" (UI callbacks, DB accessors, notifiers, third‑party fetchers).

1) Big-picture architecture
- Frontend: Streamlit pages under `app_pages/` with the orchestrator entry `board_game_manager.py`.
- UI helpers & callbacks: `utils/streamlit_utils.py` (key callbacks: `create_callback`, `join_callback`, `leave_callback`, `delete_callback`, `update_table_propositions`).
- Persistence: `utils/sql_manager.py` (class `SQLManager`) — all DB access (users, locations, table_propositions, joined_players). Note: `SQLManager.create_tables()` will initialize DB and may create a default location using DEFAULT_LOCATION_* env vars.
- External integrations: BGG (BGG API helper `utils/bgg_manager.py`), Telegram notifications (`utils/telegram_notifications.py`).
- Domain objects and UI adapters: `utils/table_system_proposition.py`, `utils/table_system_user.py`, `utils/table_system_location.py`.

2) Critical developer workflows / run commands
- Run app locally: `streamlit run board_game_manager.py` (also documented in `README.md`).
- Install deps: `pip install -r requirements.txt`.
- DB bootstrap: happens automatically when `utils.streamlit_utils` is imported (it instantiates `SQLManager()` and calls `create_tables()`). Ensure DB env vars are set before the first import to avoid exceptions.

3) Project-specific conventions & patterns (concrete)
- Streamlit session-driven pattern: heavy use of `st.session_state` (e.g. `st.session_state.user`, `propositions`, `username`, `location`, `proposition_type`). Agents must read/update `session_state` and call `StreamlitTablePropositions.refresh_table_propositions(...)` to force UI refresh.
- Callback recipe: UI -> callback in `streamlit_utils.py` -> call `sql_manager` methods -> send notifications via `TelegramNotifications` -> call `StreamlitTablePropositions.refresh_table_propositions` and `st.toast` for feedback. See `create_callback` (file: `utils/streamlit_utils.py`) for full example.
- Import-time side-effects: `utils/streamlit_utils.py` instantiates `SQLManager()` and `TelegramNotifications()` at module import (lines near top) and immediately runs `sql_manager.create_tables()`. Any agent that imports these modules must be aware this triggers DB and network side effects.
- DB constraint enforcement: `sql_manager.create_tables()` creates a PostgreSQL trigger/function `check_max_players()` used to prevent joins beyond max players — errors surface as psycopg2 exceptions and are wrapped into user-friendly AttributeError messages (see `join_table`).

4) Integration points & environment variables (examples)
- PostgreSQL: credentials via DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, DB_SCHEMA (read in `utils/sql_manager.py`).
- Telegram: TELEGRAM_BOT_TOKEN and several chat id env vars (TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID_PROPOSITION_DEFAULT, *_ROW, *_TOURNAMENT, *_DEMO) — chat id strings may include a thread `_N` suffix parsed in `TelegramNotifications._get_chat_id`.
- BGG: BGG_API_BEARER_TOKEN and BGG_URL are used in `utils/bgg_manager.py` and `streamlit_utils.py`.
- App settings: TITLE, DEFAULT_DATE, DEFAULT_LOCATION_* (see `README.md` and `sql_manager.create_tables`), CAN_ADMIN_CREATE_TOURNAMENT / CAN_ADMIN_CREATE_DEMO (toggle pages in `board_game_manager.py` and `streamlit_utils.get_table_proposition_types`).

5) Agent catalog — quick entry points (concrete files & functions)
- Create proposition: `utils.streamlit_utils.create_callback(game_name, bgg_game_id, image_url)` — shows full flow: persist via `sql_manager.create_proposition`, call `telegram_bot.send_new_table_message`, then `StreamlitTablePropositions.refresh_table_propositions`.
- Update proposition: `utils.streamlit_utils.update_table_propositions(...)` → `sql_manager.update_table_proposition` + `telegram_bot.send_update_table_message`.
- Join/Leave/Delete: `utils.streamlit_utils.join_callback`, `leave_callback`, `delete_callback` (call `sql_manager.join_table`, `leave_table`, `delete_proposition` respectively). `join_table` raises AttributeError on duplicate join or max players exceeded.
- DB access: `utils.sql_manager.SQLManager` methods: `create_tables()`, `create_proposition(...)`, `join_table(...)`, `leave_table(...)`, `get_table_propositions()` — preferred single place for DB changes.
- Telegram: `utils.telegram_notifications.TelegramNotifications.send_new_table_message(...)` and `send_update_table_message(...)` — returns `TelegramNotificationsOutput` with .skipped/.message_id/.error which callers check to show toasts.
- BGG: `utils.bgg_manager.get_bgg_game_info(game_id)` and `search_bgg_games(name)` — decorated with `@cache_data` (streamlit cache). Respect TTL and caching semantics when testing.

6) How to add a new agent (practical recipe)
- 1) Add UI element in `app_pages/` or update `board_game_manager.py` page listing.
- 2) Implement callback in `utils/streamlit_utils.py` following existing patterns: call the appropriate `sql_manager` method, call `telegram_bot` if notification is required, then call `StreamlitTablePropositions.refresh_table_propositions(reason, table_id=...)` and `st.toast(...)` for user feedback.
- 3) Put DB logic into `utils/sql_manager.py` (new methods there) so all SQL lives in one place. Create migration-like SQL in `create_tables()` only if it's a schema addition that can be safely run on import.
- 4) Test locally: ensure DB env vars point to a local Postgres, run `streamlit run board_game_manager.py`, exercise the UI; watch logs in `utils/table_system_logging.py`.

7) Warnings & gotchas for autonomous agents
- Avoid importing `utils.streamlit_utils` in analysis-only code without env vars set — it will call `create_tables()` and may raise AttributeError if DEFAULT_LOCATION_* are missing.
- Telegram chat ids may include a thread suffix `_N`; parsing happens in `TelegramNotifications._get_chat_id` — use that helper rather than re-parsing strings yourself.
- Respect `st.session_state` keys used across modules: `user`, `username`, `propositions`, `location`, `proposition_type`, `god_mode`.

References: files worth opening for concrete examples
- board_game_manager.py, README.md
- utils/streamlit_utils.py, utils/sql_manager.py, utils/telegram_notifications.py, utils/bgg_manager.py
- utils/table_system_proposition.py and utils/table_system_user.py (UI <-> domain mappings)

If you want I can expand any catalog entry into a step-by-step change (patch + tests) for adding a new notification or DB-backed agent.


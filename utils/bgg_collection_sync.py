"""Background job that syncs each user's *owned* games from BGG into the local Postgres DB.

Design / requirements:
- BGG enforces a very low API rate, so we query at most one user per ``per_user_delay_seconds``
  (default 60s -> 1 request/min).
- The whole sync runs once a day AND once at app startup, in a **non-blocking** way (daemon thread).
- For each user that has a BGG username set, the job fetches the owned collection, deletes the
  previously stored list for that user and inserts the fresh one (with a ``last_updated`` timestamp),
  then moves on to the next user after the rate-limit delay.

The job is started as a process-wide singleton via ``start_bgg_collection_sync()``, which is meant to
be called through ``streamlit.cache_resource`` so it runs exactly once per Streamlit server process
(and not once per session/rerun).
"""

import os
import threading
import time

from utils.table_system_logging import logging
from utils.sql_manager import SQLManager
from utils.bgg_manager import get_bgg_owned_games, BGGCollectionQueuedError


def _str_to_bool(s: str) -> bool:
    return str(s).lower() == 'true'


class BGGCollectionSyncJob:
    """Encapsulates the daemon thread that periodically syncs BGG owned collections."""

    def __init__(self, per_user_delay_seconds=None, period_hours=None):
        # 1 request/min by default to respect BGG's low rate limit.
        self.per_user_delay_seconds = per_user_delay_seconds if per_user_delay_seconds is not None else \
            int(os.getenv("BGG_COLLECTION_SYNC_PER_USER_DELAY_SECONDS", 60))
        # Re-run the whole sync once a day by default.
        self.period_hours = period_hours if period_hours is not None else \
            float(os.getenv("BGG_COLLECTION_SYNC_PERIOD_HOURS", 24))

        self.sql_manager = SQLManager()
        self._thread = None
        self._lock = threading.Lock()
        self._started = False

    def start(self):
        """Start the background daemon thread once (idempotent, thread-safe)."""
        with self._lock:
            if self._started:
                return
            self._started = True
            self._thread = threading.Thread(
                target=self._run_loop,
                name="bgg-collection-sync",
                daemon=True,
            )
            self._thread.start()
            logging.info(
                f"BGG collection sync job started "
                f"(per_user_delay={self.per_user_delay_seconds}s, period={self.period_hours}h)"
            )

    def _run_loop(self):
        """Run a sync cycle immediately (at startup) and then once every ``period_hours``."""
        while True:
            try:
                self.run_sync_cycle()
            except Exception as e:
                # Never let the loop die: log and wait for the next scheduled run.
                logging.error(f"BGG collection sync cycle failed: {e}")
            time.sleep(max(self.period_hours, 0) * 3600)

    def run_sync_cycle(self):
        """Sync the owned collection of every user that has a BGG username, one per rate-limit slot."""
        try:
            users = self.sql_manager.get_users_with_bgg_username(use_streamlit_error=False)
        except Exception as e:
            logging.error(f"BGG collection sync: could not list users: {e}")
            return

        logging.info(f"BGG collection sync: starting cycle for {len(users)} user(s) with a BGG username")

        for index, (user_id, username, bgg_username) in enumerate(users):
            self._sync_single_user(user_id, username, bgg_username)
            # Rate limit: wait before querying the next user (skip the wait after the last one).
            if index < len(users) - 1:
                time.sleep(self.per_user_delay_seconds)

        logging.info("BGG collection sync: cycle completed")

    def _sync_single_user(self, user_id, username, bgg_username):
        try:
            games = get_bgg_owned_games(bgg_username)
        except BGGCollectionQueuedError as e:
            logging.warning(f"BGG collection sync: skipping user '{username}' ({bgg_username}) this cycle: {e}")
            return
        except Exception as e:
            logging.error(f"BGG collection sync: error fetching collection for '{bgg_username}': {e}")
            return

        try:
            self.sql_manager.replace_owned_games(user_id, games, use_streamlit_error=False)
            logging.info(
                f"BGG collection sync: stored {len(games)} owned game(s) for "
                f"user '{username}' (BGG: {bgg_username})"
            )
        except Exception as e:
            logging.error(f"BGG collection sync: error saving collection for '{bgg_username}': {e}")


def start_bgg_collection_sync():
    """Create and start the singleton sync job. Returns the job instance (or None if disabled).

    Meant to be wrapped by ``st.cache_resource`` so it runs once per Streamlit server process.
    Disable entirely by setting the env var ``BGG_COLLECTION_SYNC_ENABLED=false``.
    """
    if not _str_to_bool(os.getenv("BGG_COLLECTION_SYNC_ENABLED", "true")):
        logging.info("BGG collection sync is disabled (BGG_COLLECTION_SYNC_ENABLED=false)")
        return None

    job = BGGCollectionSyncJob()
    job.start()
    return job

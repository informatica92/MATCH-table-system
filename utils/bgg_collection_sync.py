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

        # Record the start of this job run (best effort: never block the sync if logging fails).
        log_id = None
        try:
            log_id = self.sql_manager.start_sync_log(len(users), use_streamlit_error=False)
        except Exception as e:
            logging.error(f"BGG collection sync: could not open sync log: {e}")

        total = len(users)
        users_synced = 0
        users_failed = 0
        last_completed_cycle_timestamp = self.sql_manager.get_last_completed_sync().get('finished_at')
        try:
            if last_completed_cycle_timestamp is not None and (time.time() - last_completed_cycle_timestamp.timestamp()) < self.period_hours * 3600:
                logging.info(
                    f"BGG collection sync: skipping cycle because last completed cycle was less than "
                    f"{self.period_hours}h ({self.period_hours/24}days) ago"
                )
            else:
                for index, (user_id, username, bgg_username, last_updated) in enumerate(users):
                    if last_updated is not None and (time.time() - last_updated.timestamp()) < self.period_hours * 3600:
                        logging.info(
                            f"BGG collection sync: [{index+1}/{total}] skipping user '{username}' ({bgg_username}) "
                            f"because last update was less than {self.period_hours}h ({self.period_hours/24}days) ago"
                        )
                        continue
                    if self._sync_single_user(user_id, username, bgg_username, index=index, total=total):
                        users_synced += 1
                    else:
                        users_failed += 1
                    # Rate limit: wait before querying the next user (skip the wait after the last one).
                    if index < total - 1:
                        time.sleep(self.per_user_delay_seconds)
        except Exception as e:
            if log_id is not None:
                try:
                    self.sql_manager.finish_sync_log(log_id, 'failed', users_synced, users_failed, error=str(e), use_streamlit_error=False)
                except Exception as log_e:
                    logging.error(f"BGG collection sync: could not close sync log: {log_e}")
            raise

        if log_id is not None:
            try:
                self.sql_manager.finish_sync_log(log_id, 'completed', users_synced, users_failed, use_streamlit_error=False)
            except Exception as e:
                logging.error(f"BGG collection sync: could not close sync log: {e}")

        logging.info(f"BGG collection sync: cycle completed ({users_synced} synced, {users_failed} failed)")

    def _sync_single_user(self, user_id, username, bgg_username, index=0, total=1):
        """Sync one user's owned collection. Returns True on success, False on failure/skip."""
        try:
            # get_bgg_owned_games issues two BGG calls (base games + expansions); space them out by the
            # same per-user delay so every request stays within the configured rate limit.
            games = get_bgg_owned_games(bgg_username, inter_call_delay_seconds=self.per_user_delay_seconds)
        except BGGCollectionQueuedError as e:
            logging.warning(f"BGG collection sync: [{index + 1}/{total}] skipping user '{username}' ({bgg_username}) this cycle: {e}")
            return False
        except Exception as e:
            logging.error(f"BGG collection sync: [{index + 1}/{total}] error fetching collection for '{bgg_username}': {e}")
            return False

        try:
            self.sql_manager.replace_owned_games(user_id, games, use_streamlit_error=False)
            logging.info(f"BGG collection sync: [{index + 1}/{total}] stored {len(games)} owned game(s) for user '{username}' (BGG: {bgg_username})")
            return True
        except Exception as e:
            logging.error(f"BGG collection sync: [{index + 1}/{total}] error saving collection for '{bgg_username}': {e}")
            return False


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

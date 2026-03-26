"""Redis client — writes word counts and metadata to Redis."""

import logging
import random
import time
from datetime import datetime, timezone

import redis

from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_KEY_RANKING,
    REDIS_KEY_REPOS,
    REDIS_KEY_TOTAL,
    REDIS_KEY_STATUS,
)

logger = logging.getLogger(__name__)


class RedisClient:
    """Handles all write operations to Redis.

    Single Responsibility: only writes word counts and miner metadata.
    The Visualizer has its own read-only client — they never share instances.
    """

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        max_retries: int = 10,
        retry_delay: int = 3,
    ) -> None:
        self._conn = self._connect(host, port, max_retries, retry_delay)

    @staticmethod
    def _connect(
        host: str, port: int, max_retries: int, retry_delay: int
    ) -> redis.Redis:
        """Connect to Redis with retry, exponential backoff, and jitter."""
        for attempt in range(1, max_retries + 1):
            try:
                conn = redis.Redis(host=host, port=port, decode_responses=True)
                conn.ping()
                logger.info("Connected to Redis at %s:%d", host, port)
                return conn
            except redis.exceptions.RedisError as e:
                base_wait = retry_delay * (2 ** (attempt - 1))
                wait = base_wait + random.uniform(0, 1)
                logger.warning(
                    "Redis unavailable: %s (attempt %d/%d), retrying in %.2fs",
                    e, attempt, max_retries, wait,
                )
                time.sleep(wait)

        raise ConnectionError(
            f"Could not connect to Redis at {host}:{port} after {max_retries} attempts."
        )

    # -- Public API -----------------------------------------------------------

    def store_words(self, words: list[str], repo: str, language: str = "") -> None:
        """Increment the score of each word in the ranking and update metadata.

        Uses a pipeline to batch all commands into a single round-trip,
        which is significantly faster than sending them one by one.
        When *language* is provided, words are also written to a
        language-specific sorted set (e.g. ``word_ranking:python``).
        """
        if not words:
            return

        lang_key = f"{REDIS_KEY_RANKING}:{language}" if language else ""

        pipe = self._conn.pipeline()

        for word in words:
            pipe.zincrby(REDIS_KEY_RANKING, 1, word)
            if lang_key:
                pipe.zincrby(lang_key, 1, word)

        pipe.sadd(REDIS_KEY_REPOS, repo)
        pipe.incrby(REDIS_KEY_TOTAL, len(words))

        pipe.execute()

    def update_status(self, current_repo: str) -> None:
        """Write the current miner status to a Redis hash."""
        self._conn.hset(REDIS_KEY_STATUS, mapping={
            "current_repo": current_repo,
            "running": "true",
            "last_update": datetime.now(timezone.utc).isoformat(),
        })

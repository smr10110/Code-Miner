"""Read-only Redis client for the Visualizer.

Single Responsibility: only reads data that the Miner has written.
Never writes to Redis — that is the Miner's job.
"""

import logging
import time

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


class RedisReader:
    """Provides read-only access to the word ranking and metadata in Redis."""

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT) -> None:
        self._conn = self._connect(host, port)

    @staticmethod
    def _connect(host: str, port: int, max_retries: int = 15, delay: int = 2) -> redis.Redis:
        """Connect to Redis with retry logic."""
        for attempt in range(1, max_retries + 1):
            try:
                conn = redis.Redis(host=host, port=port, decode_responses=True)
                conn.ping()
                logger.info("Connected to Redis at %s:%d", host, port)
                return conn
            except redis.ConnectionError:
                logger.warning(
                    "Redis unavailable (attempt %d/%d), retrying in %ds",
                    attempt, max_retries, delay,
                )
                time.sleep(delay)

        raise ConnectionError(f"Could not connect to Redis at {host}:{port}")

    def get_ranking(self, top_n: int, language: str = "") -> list[dict]:
        """Return the top-N words ordered by count descending.

        When *language* is provided (e.g. "python", "java"), reads from
        the language-specific sorted set instead of the overall ranking.
        """
        key = f"{REDIS_KEY_RANKING}:{language}" if language else REDIS_KEY_RANKING
        raw = self._conn.zrevrange(key, 0, top_n - 1, withscores=True)
        return [
            {"word": word, "count": int(score), "rank": rank}
            for rank, (word, score) in enumerate(raw, 1)
        ]

    def get_stats(self) -> dict:
        """Return aggregate statistics from multiple Redis keys."""
        status = self._conn.hgetall(REDIS_KEY_STATUS)
        return {
            "total_words": int(self._conn.get(REDIS_KEY_TOTAL) or 0),
            "unique_words": self._conn.zcard(REDIS_KEY_RANKING),
            "repos_processed": self._conn.scard(REDIS_KEY_REPOS),
            "miner_status": status.get("running", "stopped"),
            "current_repo": status.get("current_repo", ""),
        }

    def get_repos(self) -> list[str]:
        """Return a sorted list of all processed repository names."""
        return sorted(self._conn.smembers(REDIS_KEY_REPOS))

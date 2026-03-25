"""Centralized configuration for the Visualizer component."""

import os

# -- Redis --------------------------------------------------------------------

REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

# Keys must match what the Miner writes
REDIS_KEY_RANKING: str = "word_ranking"
REDIS_KEY_REPOS: str = "processed_repos"
REDIS_KEY_TOTAL: str = "total_words_sent"
REDIS_KEY_STATUS: str = "miner_status"

# -- API defaults -------------------------------------------------------------

DEFAULT_TOP_N: int = int(os.getenv("DEFAULT_TOP_N", "10"))
API_BASE: str = os.getenv("API_BASE", "http://localhost:8000")

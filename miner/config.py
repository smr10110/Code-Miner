"""Centralized configuration — single source of truth for all settings.

Every tunable value lives here. Modules import from config instead of
reading environment variables or hardcoding values themselves.
This keeps the codebase easy to maintain: change one file, not ten.
"""

import os

# -- GitHub API ---------------------------------------------------------------

GITHUB_API_URL: str = os.getenv("GITHUB_API_URL", "https://api.github.com")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
REPOS_PER_PAGE: int = int(os.getenv("REPOS_PER_PAGE", "30"))
MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "3"))
SOURCE_EXTENSIONS: tuple[str, ...] = (".py", ".java")

# Minimum stars a repo must have to be mined (avoids tiny/empty repos).
MIN_STARS: int = int(os.getenv("MIN_STARS", "100"))

# -- Redis --------------------------------------------------------------------

REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_KEY_RANKING: str = "word_ranking"
REDIS_KEY_REPOS: str = "processed_repos"
REDIS_KEY_TOTAL: str = "total_words_sent"
REDIS_KEY_STATUS: str = "miner_status"

# Map file extensions to language names (used for per-language ranking keys).
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".java": "java",
}

# -- Word filtering -----------------------------------------------------------
# Words to exclude from the ranking (too common or meaningless).

STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "it", "to", "of", "in", "on",
    "and", "or", "not", "no", "do", "if", "else",
    "for", "while", "with", "as", "from", "import",
    "true", "false", "none", "null",
    "self", "cls", "this",
    "args", "kwargs",
    # Common but meaningless function name fragments
    "test", "tests", "init", "setup", "teardown", "main",
})

# -- Java parser --------------------------------------------------------------
# Java keywords that the regex may falsely match as method names.

JAVA_KEYWORDS: frozenset[str] = frozenset({
    "if", "else", "for", "while", "do", "switch", "case",
    "return", "new", "throw", "catch", "try",
    "Exception", "String", "Object", "Integer", "Boolean",
})

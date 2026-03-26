"""Miner entry point — infinite loop that mines GitHub repos."""

import logging

from config import (
    GITHUB_API_URL,
    GITHUB_TOKEN,
    REPOS_PER_PAGE,
    MAX_DEPTH,
    SOURCE_EXTENSIONS,
    MIN_STARS,
    EXTENSION_TO_LANGUAGE,
)
from github_client import GitHubClient
from parser_python import extract_functions as parse_python
from parser_java import extract_functions as parse_java
from word_splitter import split_name
from redis_client import RedisClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Map file extensions to their parser function.
# Both parsers share the same signature: (source: str) -> list[str]
PARSERS = {
    ".py": parse_python,
    ".java": parse_java,
}


def _get_parser(file_path: str):
    """Return (parser, language) for a file, or (None, "") if unsupported."""
    for ext, parser in PARSERS.items():
        if file_path.endswith(ext):
            return parser, EXTENSION_TO_LANGUAGE.get(ext, "")
    return None, ""


def _process_repo(
    github: GitHubClient, store: RedisClient, owner: str, repo: str
) -> None:
    """Download, parse, and store words from a single repository."""
    full_name = f"{owner}/{repo}"
    store.update_status(full_name)

    total_words = 0

    for file_path, content in github.get_source_files(
        owner, repo, SOURCE_EXTENSIONS, MAX_DEPTH
    ):
        parser, language = _get_parser(file_path)
        if parser is None:
            continue

        function_names = parser(content)
        words = []
        for name in function_names:
            words.extend(split_name(name))

        if words:
            store.store_words(words, full_name, language)
            total_words += len(words)

    logger.info("Repo %s: stored %d words", full_name, total_words)


def _mine_page(
    github: GitHubClient, store: RedisClient, page: int
) -> int:
    """Mine all repos from a single search page. Returns number of repos found."""
    repos = github.search_repos(
        page=page, per_page=REPOS_PER_PAGE,
        min_stars=MIN_STARS,
    )

    supported_languages = set(EXTENSION_TO_LANGUAGE.values())

    for repo_data in repos:
        full_name = repo_data["full_name"]
        stars = repo_data.get("stargazers_count", 0)
        repo_language = (repo_data.get("language") or "").lower()

        if repo_language not in supported_languages:
            logger.info("Skipping %s (language: %s)", full_name, repo_language or "unknown")
            continue

        owner, repo = full_name.split("/")
        logger.info("Mining repo: %s (stars: %d, language: %s)", full_name, stars, repo_language)

        try:
            _process_repo(github, store, owner, repo)
        except Exception:
            logger.exception("Error mining %s, skipping", full_name)

    return len(repos)


def main() -> None:
    """Infinite mining loop — alternates languages and pages forever."""
    logger.info("Miner starting up")

    github = GitHubClient(base_url=GITHUB_API_URL, token=GITHUB_TOKEN)
    store = RedisClient()

    logger.info("All connections ready, starting mining loop")

    page = 1

    try:
        while True:
            found = _mine_page(github, store, page)

            if found == 0:
                logger.info("No more repos on page %d, resetting", page)
                page = 1
            else:
                page += 1

    except KeyboardInterrupt:
        logger.info("Miner stopped by user")
    finally:
        github.close()


if __name__ == "__main__":
    main()

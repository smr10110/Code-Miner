"""GitHub API client — searches repos and downloads source files."""

import base64
import logging
import time
from typing import Generator

import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """Encapsulates all interaction with the GitHub REST API.

    Responsibilities:
      - Search repositories by language.
      - Traverse repo trees up to a configurable depth.
      - Download and decode individual source files.
      - Handle rate-limiting transparently.
    """

    def __init__(self, base_url: str, token: str = "", timeout: int = 30) -> None:
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        
    def search_repos(
        self,
        language: str,
        page: int = 1,
        per_page: int = 30,
        min_stars: int = 50,
    ) -> list[dict]:
        """Search repos with recent activity, sorted by stars descending.

        Filters repos pushed in the last 30 days with at least *min_stars*.
        """
        query = f"language:{language} stars:>={min_stars}"

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        }

        resp = self._get("/search/repositories", params=params)
        items = resp.json().get("items", [])
        logger.info(
            "Search page %d for %s: %d repos found",
            page, language, len(items),
        )
        return items

    def get_source_files(
        self,
        owner: str,
        repo: str,
        extensions: tuple[str, ...] = (".py", ".java"),
        max_depth: int = 3,
    ) -> Generator[tuple[str, str], None, None]:
        """Traverse a repo (DFS, up to *max_depth*) and yield (path, content).

        Only files whose name ends with one of *extensions* are downloaded.
        """
        # Stack of (directory_path, current_depth)
        stack: list[tuple[str, int]] = [("", 0)]
        files_found = 0

        while stack:
            current_path, depth = stack.pop()
            if depth > max_depth:
                continue

            for item in self._list_dir(owner, repo, current_path):
                result = self._process_item(item, depth, max_depth, extensions, stack)
                if result is not None:
                    files_found += 1
                    yield result

        logger.info("Found %d source files in %s/%s", files_found, owner, repo)

    def _process_item(
        self,
        item: dict,
        depth: int,
        max_depth: int,
        extensions: tuple[str, ...],
        stack: list[tuple[str, int]],
    ) -> tuple[str, str] | None:
        """Classify a directory item and return (path, content) if it is a source file."""
        if item["type"] == "dir" and depth < max_depth:
            stack.append((item["path"], depth + 1))
            return None

        if item["type"] == "file" and self._matches(item["name"], extensions):
            content = self._download_file(item["url"])
            if content is not None:
                return item["path"], content

        return None

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
        
    def _get(self, path: str, **kwargs) -> httpx.Response:
        """Perform a GET request and handle rate limiting."""
        resp = self._client.get(path, **kwargs)
        self._handle_rate_limit(resp)
        resp.raise_for_status()
        return resp

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Sleep if the rate limit is exhausted."""
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        reset_ts = int(response.headers.get("X-RateLimit-Reset", 0))

        if remaining <= 1 and reset_ts:
            sleep_for = max(reset_ts - int(time.time()), 1) + 1
            logger.info("Rate limit: %d remaining, reset in %ds", remaining, sleep_for)
            time.sleep(sleep_for)

    def _list_dir(self, owner: str, repo: str, path: str = "") -> list[dict]:
        """List contents of a single directory in a repo."""
        url = f"/repos/{owner}/{repo}/contents/{path}"
        resp = self._client.get(url)
        self._handle_rate_limit(resp)

        if resp.status_code != 200:
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    def _download_file(self, file_api_url: str) -> str | None:
        """Download a file via its API URL and decode from base64."""
        resp = self._client.get(file_api_url)
        self._handle_rate_limit(resp)

        if resp.status_code != 200:
            return None

        content_b64 = resp.json().get("content", "")
        if not content_b64:
            return None

        try:
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Error decoding file: %s", exc)
            return None

    @staticmethod
    def _matches(filename: str, extensions: tuple[str, ...]) -> bool:
        """Check if a filename ends with any of the given extensions."""
        return any(filename.endswith(ext) for ext in extensions)

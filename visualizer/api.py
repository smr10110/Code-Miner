"""Visualizer API — FastAPI routes that expose Redis data over HTTP.

Single Responsibility: only handles HTTP request/response.
All data access is delegated to RedisReader.
"""

from typing import Annotated

from fastapi import FastAPI, Query

from config import DEFAULT_TOP_N
from redis_reader import RedisReader

app = FastAPI(title="GitHub Word Miner — Visualizer API")
reader = RedisReader()


@app.get("/health")
def health():
    """Simple liveness check for Docker healthcheck."""
    return {"status": "ok"}


@app.get("/ranking")
def ranking(
    top_n: Annotated[int, Query(ge=1, le=500)] = DEFAULT_TOP_N,
    language: Annotated[str, Query()] = "",
):
    """Return the top-N words from the ranking.

    Pass ``language=python`` or ``language=java`` to filter by language.
    Omit or leave empty for the overall ranking.
    """
    return {
        "ranking": reader.get_ranking(top_n, language),
        "top_n": top_n,
        "language": language or "all",
    }


@app.get("/stats")
def stats():
    """Return aggregate mining statistics."""
    return reader.get_stats()


@app.get("/repos")
def repos():
    """Return the list of all processed repositories."""
    return {"repos": reader.get_repos()}

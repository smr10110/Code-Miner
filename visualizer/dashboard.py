"""Streamlit dashboard — live updates via st.fragment.

Single Responsibility: only renders the UI.
All data comes from the FastAPI API running on localhost:8000.
Uses streamlit-echarts for interactive charts (same style as plantilla.py).
"""

import requests
import streamlit as st
from streamlit_echarts import st_echarts

from config import API_BASE


# -- Data fetching ------------------------------------------------------------

def _fetch_ranking(top_n: int, language: str = "") -> list[dict]:
    params = {"top_n": top_n}
    if language:
        params["language"] = language
    try:
        resp = requests.get(f"{API_BASE}/ranking", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json().get("ranking", [])
    except requests.RequestException:
        return []


def _fetch_stats() -> dict:
    try:
        resp = requests.get(f"{API_BASE}/stats", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {}


def _fetch_repos() -> list[str]:
    try:
        resp = requests.get(f"{API_BASE}/repos", timeout=5)
        resp.raise_for_status()
        return resp.json().get("repos", [])
    except requests.RequestException:
        return []


# -- Page config --------------------------------------------------------------

st.set_page_config(page_title="GitHub Word Miner", page_icon="⛏️", layout="wide")

# -- Sidebar ------------------------------------------------------------------

LANGUAGE_OPTIONS = {"All": "", "Python": "python", "Java": "java"}

with st.sidebar:
    st.title("⛏️ Controls")
    top_n = st.selectbox("Top N Words", options=[5, 10, 15, 20, 30, 50], index=1)
    lang_label = st.selectbox("Language", options=list(LANGUAGE_OPTIONS.keys()))
    lang_filter = LANGUAGE_OPTIONS[lang_label]


# -- Live data fragment (re-runs every 2s without reloading the page) ---------

@st.fragment(run_every=0.5)
def live_dashboard():
    """Fetch data and render the full dashboard. Runs every 2 seconds."""
    stats = _fetch_stats()
    ranking = _fetch_ranking(top_n, lang_filter)
    repos = _fetch_repos()

    # -- Header ---------------------------------------------------------------

    is_running = stats.get("miner_status") == "true" if stats else False
    status = "🟢 Mining Active" if is_running else "🔴 Miner Stopped"

    st.title("⛏️ GitHub Word Miner")
    st.caption(status)

    # -- Metrics (same style as plantilla.py) ---------------------------------

    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Words", f'{stats.get("total_words", 0):,}', border=True)
        c2.metric("Unique Words", f'{stats.get("unique_words", 0):,}', border=True)
        c3.metric("Repos Scanned", stats.get("repos_processed", 0), border=True)
        c4.metric("Current Repo", stats.get("current_repo", "—"), border=True)

    # -- Chart and side panel -------------------------------------------------

    if not ranking:
        st.info("⏳ Waiting for data from the Miner...")
        return

    col_chart, col_side = st.columns([3, 1])

    with col_chart:
        words = [item["word"] for item in ranking]
        counts = [item["count"] for item in ranking]

        bar_opts = {
            "title": {"text": "Word Frequency Ranking", "left": "center"},
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"},
            },
            "grid": {
                "left": "3%",
                "right": "10%",
                "bottom": "3%",
                "containLabel": True,
            },
            "xAxis": {"type": "value", "name": "Count"},
            "yAxis": {
                "type": "category",
                "data": words[::-1],
                "axisLabel": {"fontFamily": "monospace"},
            },
            "series": [
                {
                    "type": "bar",
                    "data": counts[::-1],
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 1, "y2": 0,
                            "colorStops": [
                                {"offset": 0, "color": "#5470c6"},
                                {"offset": 1, "color": "#91cc75"},
                            ],
                        },
                        "borderRadius": [0, 4, 4, 0],
                    },
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}",
                        "fontFamily": "monospace",
                    },
                }
            ],
        }
        st_echarts(
            options=bar_opts,
            height=f"{max(300, len(ranking) * 32)}px",
            key="ranking_bar",
        )

    with col_side:
        # Summary
        if stats and ranking:
            st.subheader("Summary")
            st.metric("Top Word", ranking[0]["word"], border=True)
            st.metric("Top Count", f'{ranking[0]["count"]:,}', border=True)
            st.metric("Total Mined", f'{stats.get("total_words", 0):,}', border=True)

        # Recent repos
        if repos:
            st.subheader("Recent Repos")
            for repo_name in repos[-10:]:
                st.text(repo_name)


live_dashboard()

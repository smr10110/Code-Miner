"""Word splitter — breaks function names into individual words."""

import re

from config import STOP_WORDS

# Regex to split camelCase and PascalCase into words.
#
# It handles three patterns (evaluated left to right):
#   [A-Z]+(?=[A-Z][a-z])  → acronym followed by a new word:  "HTTPSConnection" → "HTTPS", "Connection"
#   [A-Z]?[a-z]+          → regular word, optionally starting uppercase: "get", "User"
#   [A-Z]+                → trailing acronym: "JSON" at end of string
#   [0-9]+                → numeric sequences: "v2" → "2"
_CAMEL_PATTERN = re.compile(
    r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+"
)


def split_name(function_name: str) -> list[str]:
    """Split a function/method name into lowercase words.

    Algorithm:
      1. Split by underscores (handles snake_case and leading/trailing _)
      2. For each fragment, split by camelCase using regex
      3. Lowercase everything and filter empty strings

    Examples:
      "make_response"    → ["make", "response"]
      "getUserById"      → ["get", "user", "by", "id"]
      "parseJSON"        → ["parse", "json"]
      "__init__"         → ["init"]
      "HTTPSConnection"  → ["https", "connection"]
    """
    words: list[str] = []

    # Step 1: split by underscores
    fragments = function_name.split("_")

    for fragment in fragments:
        if not fragment:
            continue

        # Step 2: split each fragment by camelCase
        parts = _CAMEL_PATTERN.findall(fragment)
        words.extend(parts)

    # Step 3: lowercase everything and filter stop words
    return [w.lower() for w in words if w.lower() not in STOP_WORDS]

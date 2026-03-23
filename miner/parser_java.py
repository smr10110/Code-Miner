"""Java source parser — extracts method names using regex."""

import logging
import re

from config import JAVA_KEYWORDS

logger = logging.getLogger(__name__)

# Regex to match Java method declarations.
#
# Breakdown:
#   (?:public|private|protected|...)\s+  → optional modifiers (one or more)
#   [\w<>\[\].]+\s+                      → return type (e.g. void, List<String>, int[])
#   (\w+)                                → method name (capture group 1)
#   \s*\(                                → opening parenthesis of parameter list
#
# Examples it matches:
#   "public void run("           → "run"
#   "private static int getId("  → "getId"
#   "List<String> getNames("     → "getNames"
_METHOD_PATTERN = re.compile(
    r"(?:public|private|protected|static|final|abstract|synchronized|native|\s)+"
    r"[\w<>\[\].]+\s+"
    r"(\w+)\s*\("
)


def extract_functions(source: str) -> list[str]:
    """Extract method names from Java source code via regex.

    Returns an empty list if the source cannot be decoded.
    Filters out Java keywords that the regex may falsely match.
    """
    try:
        matches = _METHOD_PATTERN.findall(source)
    except Exception:
        return []

    return [name for name in matches if name not in JAVA_KEYWORDS]

"""Python source parser — extracts function names using the ast module."""

import ast
import logging

logger = logging.getLogger(__name__)


class _FunctionNameVisitor(ast.NodeVisitor):
    """AST visitor that collects function and async function names.

    Walks the entire syntax tree and records every FunctionDef
    and AsyncFunctionDef node name it encounters.
    """

    def __init__(self) -> None:
        self.names: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.append(node.name)
        # Continue visiting child nodes (nested functions)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.append(node.name)
        self.generic_visit(node)


def extract_functions(source: str) -> list[str]:
    """Parse Python source code and return all function/method names.

    If the source has syntax errors, returns an empty list instead
    of crashing — the miner must keep running on bad files.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    visitor = _FunctionNameVisitor()
    visitor.visit(tree)
    return visitor.names

"""Shared traversal and filtering utilities for language annotators."""

from collections.abc import Generator

from ...node import Node


def walk(node: Node) -> Generator[Node, None, None]:
    """Yield every node in post-order (children before parent).

    Post-order is required by language annotators so that child nodes are
    labelled before their parent is processed.

    Args:
        node: Root of the subtree to walk.

    Yields:
        Nodes bottom-up — each child is yielded before its parent.
    """
    for child in node.children:
        yield from walk(child)
    yield node


def meaningful_children(node: Node) -> list[Node]:
    """Return child nodes excluding whitespace and newline tokens.

    Args:
        node: Node whose children should be filtered.

    Returns:
        Child nodes excluding whitespace and newline tokens.
    """
    return [child for child in node.children if child.type not in {"whitespace", "newline"}]

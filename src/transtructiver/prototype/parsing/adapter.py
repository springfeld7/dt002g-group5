"""Adapter utilities for converting Tree-sitter nodes to internal Nodes.

This module provides a conversion function that maps Tree-sitter's node
representation into the project's internal Node structure.
"""

from ..node import Node


def convert_node(ts_node, source_bytes):
    """Convert an external parser node into a local Node tree.

    The conversion is recursive. Leaf nodes (with zero children) preserve their
    text content, while non-leaf nodes have text set to None.

    Args:
        ts_node: A Tree-sitter node with .type, .child_count, .children,
            .start_byte, and .end_byte attributes.
        source_bytes: Original source code encoded as UTF-8 bytes.

    Returns:
        Node: The root of the converted Node subtree.
    """
    if ts_node.child_count == 0:
        text = source_bytes[ts_node.start_byte : ts_node.end_byte].decode("utf8")
    else:
        text = None

    return Node(
        type=ts_node.type,
        text=text,
        children=[convert_node(child, source_bytes) for child in ts_node.children],
    )

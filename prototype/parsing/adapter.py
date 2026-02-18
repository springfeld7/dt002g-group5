"""Adapter utilities for converting external parse tree nodes to internal Nodes.

This module provides a conversion function that maps an external parser's
node representation into the project's internal Node structure.
"""

from prototype.node import Node


def convert_node(ts_node):
    """Convert an external parser node into a local Node tree.

    The conversion is recursive. Leaf nodes (with zero children) preserve their
    text content, while non-leaf nodes have text set to None.

    Args:
        ts_node: An external parser node with .type, .text, .child_count, and
            .children attributes.

    Returns:
        Node: The root of the converted Node subtree.
    """
    return Node(
        type=ts_node.type,
        text=ts_node.text if ts_node.child_count == 0 else None,
        children=[convert_node(c) for c in ts_node.children]
    )

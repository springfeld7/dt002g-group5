"""Adapter for converting and annotating Tree-sitter parse trees.

This module provides the main adapter functionality that:
1. Converts Tree-sitter nodes to internal Node representation
2. Applies language-specific semantic annotations
"""

from tree_sitter import Node as TSNode

from ..node import Node
from .converter import convert_node
from .annotation import annotate


def adapt(ts_node: TSNode, source_bytes: bytes) -> Node:
    """Convert and annotate a Tree-sitter node to an internal Node.

    This is the main adapter function that performs two steps:
    1. Converts the Tree-sitter node to the internal Node representation
    2. Applies semantic annotations based on the detected language

    Args:
        ts_node (TSNode): The Tree-sitter node to adapt.
        source_bytes (bytes): The source code as bytes.

    Returns:
        Node: The converted and annotated internal Node.

    Raises:
        ValueError: If the language is not supported.
    """
    # Step 1: Convert Tree-sitter node to internal Node representation
    node = convert_node(ts_node, source_bytes)
    
    # Step 2: Apply semantic annotations based on language
    annotated_node = annotate(node)
    
    return annotated_node

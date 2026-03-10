"""Main annotator dispatcher for semantic annotation.

This module routes nodes to the appropriate language-specific annotator
based on the root node type.
"""

from ...node import Node
from .python_annotator import annotate_python
from .java_annotator import annotate_java
from .cpp_annotator import annotate_cpp


# Mapping of root node types to their respective annotators
ANNOTATOR_MAP = {
    "module": annotate_python,           # Python
    "program": annotate_java,            # Java
    "translation_unit": annotate_cpp,    # C/C++
}


def annotate(root: Node) -> Node:
    """Annotate a node tree with semantic labels based on language.

    Determines the programming language from the  node type and
    applies the appropriate language-specific semantic annotations.

    Args:
        root (Node): The root node of the syntax tree to annotate.

    Returns:
        Node: The annotated node tree with semantic labels added.

    Raises:
        ValueError: If the root node type is not recognized.
    """
    annotator = ANNOTATOR_MAP.get(root.type)
    
    if annotator is None:
        raise ValueError(
            f"No annotator found for root node type '{root.type}'. "
            f"Supported types: {list(ANNOTATOR_MAP.keys())}"
        )
    
    return annotator(root)

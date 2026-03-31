"""C-Style Indentation Strategy

Handles braced languages (Java, C++, C, etc.) where children of a block scope
are starts with a curly brace followed by a whitespace node that defines the indentation level.
"""

from .indent_strategy import IndentStrategy


class CStyleIndent(IndentStrategy):
    """
    Strategy for braced languages. Samples the 'DNA' of the code
    by looking for a whitespace child node following the opening brace.
    """

    def get_prefix(self, node) -> str:
        """
        Iterates through children to find a 'whitespace' node.
        If none exists (e.g., minified code), falls back to parent + 4.

        Args:
            node (Node): The 'block_scope' node being analyzed.

        Returns:
            str: The whitespace string to be used as a prefix for inserted code,
                 or None if no suitable prefix can be determined.
        """
        for child in node.children:
            if child.type == "whitespace":
                return child.text

        return None

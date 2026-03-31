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

    def get_prefix(self, node) -> str | None:
        """
        Iterates through children to find a newline node to guarantee there is
        vertical structure, then looks for the first 'whitespace' node
        and extracts the text as the indentation prefix.

        Args:
            node (Node): The 'block_scope' node being analyzed.

        Returns:
            str | None: The whitespace string to be used as a prefix for inserted code,
                        or None if no suitable prefix can be determined.
        """

        # Check if any of the children is a newline, which indicates that the block isn't a single-line block.
        # This might mean there is an empty block like { }, in which case it's safer to return None to avoid incorrect insertion.
        has_newline = any(child.type == "newline" for child in node.children)
        if not has_newline:
            return None

        for child in node.children:
            if child.type == "whitespace":
                return child.text

        return None

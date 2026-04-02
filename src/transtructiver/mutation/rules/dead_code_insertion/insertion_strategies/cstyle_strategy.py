"""C-Style Insertion Strategy

Handles code insertion for brace-delimited languages (C, C++, Java, etc.). 

This strategy:
* **Calculates Indentation**: Determines the required leading whitespace by 
    analyzing the block's vertical structure.
* **Validates Insertion Points**: Checks gaps between nodes to ensure 
    insertions only occur at valid logical breaks (e.g., after newlines).
* **Defines Terminal Conditions**: Identifies statements that end execution 
    within a block (like returns or breaks) to manage insertion flow.
"""

from typing import Optional

from .insertion_strategy import InsertionStrategy
from .....node import Node


class CStyleInsertionStrategy(InsertionStrategy):
    """
    Structural strategy for C-Style (C++/Java) code insertion.

    Guards against inserting code outside of braces or on the same line
    as a brace/semicolon.
    """

    def get_indent_prefix(self, node: Node) -> str | None:
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
        # This might mean there is an empty block like { },
        # in which case it's safer to return None to avoid incorrect insertion.
        has_newline = any(child.type == "newline" for child in node.children)
        if not has_newline:
            return None

        for child in node.children:
            if child.type == "whitespace":
                return child.text

        return None

    def is_valid_gap(self, current: Node, preceding: Optional[Node]) -> bool:
        """
        Validates if the current node is a valid insertion point in brace-delimited languages.

        Args:
            current (Node): The node after the gap.
            preceding (Node | None): The node before the gap.

        Returns:
            bool: True if following a newline and not before a closing brace.
        """
        # Never insert before the opening brace
        if current.type == "{":
            return False

        # Must follow a newline, but don't jam code right before the '}'
        if preceding.type == "newline":
            return True

        return False

    def is_terminal(self, node: Node) -> bool:
        """
        Identifies terminal statements for C-style blocks.

        Args:
            node (Node): The node to evaluate.

        Returns:
            bool: True for return, break, continue, or throw.
        """
        terminal_types = {
            "return_statement",
            "break_statement",
            "continue_statement",
        }
        return node.type in terminal_types

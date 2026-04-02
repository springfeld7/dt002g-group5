"""Python Insertion Strategy

Handles code insertion for indentation-based blocks in Python.

This strategy:
* **Calculates Indentation**: Derives the required prefix based on the column 
    offset of the block's start point.
* **Validates Insertion Points**: Permits placement at the very start of a 
    block or immediately following any newline node.
* **Defines Terminal Conditions**: Identifies control-flow exits and the 
    'pass' statement as boundaries to prevent redundant or dead-code insertion.
"""

from typing import Optional

from .insertion_strategy import InsertionStrategy
from .....node import Node


class PythonInsertionStrategy(InsertionStrategy):
    """
    Structural strategy for Python-specific code insertion.

    This strategy allows for insertions at the start of blocks (after the colon)
    and after any statement followed by a newline. It specifically treats the
    'pass' statement as a block terminator to avoid mutating abstract or
    placeholder methods.
    """

    def get_indent_prefix(self, node: Node) -> str | None:
        """
        In Python, the block node's start_point[1] (column) matches
        the indentation of its first logical statement.

        Args:
            node (Node): The 'block_scope' node being analyzed.

        Returns:
            str | None: The whitespace string to be used as a prefix for inserted code,
                        or None if the column information is unavailable.
        """
        if node.start_point[1] is None:
            return None

        return " " * node.start_point[1]

    def is_valid_gap(self, current: Node, preceding: Optional[Node]) -> bool:
        """
        Determines if the gap before the current node is a valid Python insertion point.

        In Python, a gap is valid if it is at the very beginning of a block
        (preceding is None) or if it follows a newline character.

        Args:
            current (Node): The node immediately following the potential insertion.
            preceding (Node | None): The node immediately preceding the insertion.

        Returns:
            bool: True if insertion is syntactically safe, False otherwise.
        """
        # At the very start of a block is always a valid gap
        if preceding is None:
            return True

        # After any newline node, ensuring the new code starts on its own line
        return preceding.type == "newline"

    def is_terminal(self, node: Node) -> bool:
        """
        Identifies statements that should halt further insertions within a block.

        Args:
            node (Node): The node to evaluate.

        Returns:
            bool: True if the node is a return, break, continue, raise, or pass.
        """
        terminal_types = {
            "return_statement",
            "break_statement",
            "continue_statement",
            "pass_statement",
        }
        return node.type in terminal_types

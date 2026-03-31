"""Python Indentation Strategy

Handles indentation discovery for Python's indentation-sensitive blocks.
"""

from .indent_strategy import IndentStrategy


class PythonIndent(IndentStrategy):
    """
    Strategy for Python. Uses the start column of the block node
    to determine the required indentation level.
    """

    def get_prefix(self, node) -> str:
        """
        In Python, the block node's start_point[1] (column) matches
        the indentation of its first logical statement.

        Args:
            node (Node): The 'block_scope' node being analyzed.

        Returns:
            str: The whitespace string to be used as a prefix for inserted code.
        """
        return " " * node.start_point[1]

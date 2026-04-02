"""Base InsertionStrategy Module

This module defines the abstract interface for language-specific 
indentation and structural discovery.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .....node import Node


class InsertionStrategy(ABC):
    """
    Abstract base class for language-specific code insertion.
    Handles structural validation, indentation, and flow control.
    """

    @abstractmethod
    def get_indent_prefix(self, node: Node) -> str:
        """
        Calculates the whitespace prefix for the inserted code.

        Args:
            node (Node): The node used as the anchor for insertion.

        Returns:
            str: The whitespace string to be used as a prefix for inserted code.
        """
        pass

    @abstractmethod
    def is_valid_gap(self, current: Node, preceding: Optional[Node]) -> bool:
        """
        Determines if the space before 'current' is a safe insertion point.

        Args:
            current (Node): The node immediately following the insertion point.
            preceding (Node | None): The node immediately preceding the insertion point, if any.

        Returns:
            bool: True if it's a valid gap for insertion, False otherwise.
        """
        pass

    @abstractmethod
    def is_terminal(self, node: Node) -> bool:
        """
        Returns True if this node prevents any further code from being
        executed in the current block (e.g., return, break, pass).

        Args:
            node (Node): The node to check.

        Returns:
            bool: True if the node is a terminal statement, False otherwise.
        """
        pass

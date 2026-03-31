"""Base Strategy Module

This module defines the abstract interface for language-specific 
indentation and structural discovery.
"""

from abc import ABC, abstractmethod


class IndentStrategy(ABC):
    """
    Abstract base class for discovering indentation prefixes in source code.
    """

    @abstractmethod
    def get_prefix(self, node) -> str:
        """
        Calculates the exact indentation string for a block.

        Args:
            node (Node): The 'block_scope' node being analyzed.

        Returns:
            str: The whitespace string to be used as a prefix for inserted code.
        """
        pass

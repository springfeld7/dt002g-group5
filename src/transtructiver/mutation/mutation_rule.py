"""mutation_rule.py

Defines the MutationRule abstract base class and the MutationRecord schema.
This module provides the interface for CST mutations and the 
reporting mechanism for tracking changes via original source coordinates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, TypedDict, List, Tuple
from .mutation_types import MutationAction
from ..node import Node


class MutationRecord(TypedDict):
    """
    Schema for recording a single mutation on a CST node.

    Attributes:
        node_id (Tuple[int, int]): The unique identifier for the node.
            - For original nodes: The (row, col) start_point.
            - For synthetic nodes: A unique negative coordinate .
        action (MutationAction): The mutation type (RENAME, DELETE, MOVE, INSERT).
        metadata (Dict[str, Any]): Operation-specific data (e.g., 'new_text').
    """

    node_id: Tuple[int, int]
    action: MutationAction
    metadata: Dict[str, Any]


class MutationRule(ABC):
    """
    Interface for CST mutation logic.

    Subclasses implement the apply method to modify a Tree-Sitter tree
    and return change records used for manifest generation.
    """

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self, root: Node) -> List[MutationRecord]:
        """
        Applies a mutation to the CST and returns a log of modifications.

        Args:
            root (Any): The root node of the tree to be mutated.

        Returns:
            List[MutationRecord]: Records of all modifications made.
        """
        pass

    def __repr__(self) -> str:
        """
        Returns a string representation of the mutation rule.

        Used for debugging and logging to identify the specific rule
        class being applied (e.g., '<ControlFlowFlattening>').
        """
        return f"<{self.name}>"

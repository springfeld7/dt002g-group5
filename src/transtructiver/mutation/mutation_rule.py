"""mutation_rule.py

Defines the MutationRule abstract base class and the LocalChangeRecord schema.
This module provides the interface for in-place CST mutations and the 
reporting mechanism for tracking changes via original source coordinates.
"""

from abc import ABC, abstractmethod
from typing import TypedDict, List, Optional, Tuple
from ..node import Node


class LocalChangeRecord(TypedDict, total=False):
    """
    Schema for recording a single mutation on a CST node.

    Attributes:
        node_id (Optional[Tuple[int, int]]): The (row, col) start_point of the
            node in the original source file. None for synthetic nodes.
        action (str): The mutation type (RENAME, DELETE, MOVE, TYPE_CHANGE, INSERT).
        metadata (dict): Operation-specific data (e.g., new_text, destination_path).
    """

    node_id: Optional[Tuple[int, int]]
    action: str
    metadata: dict


class MutationRule(ABC):
    """
    Interface for CST mutation logic.

    Subclasses implement the apply method to modify a Tree-Sitter tree
    and return change records used for manifest generation.
    """

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self, root: Node) -> List[LocalChangeRecord]:
        """
        Applies a mutation to the CST and returns a log of modifications.

        Args:
            root (Any): The root node of the tree to be mutated.

        Returns:
            List[LocalChangeRecord]: Records of all modifications made.
        """
        pass

    def __repr__(self) -> str:
        """
        Returns a string representation of the mutation rule.

        Used for debugging and logging to identify the specific rule
        class being applied (e.g., '<ControlFlowFlattening>').
        """
        return f"<{self.name}>"

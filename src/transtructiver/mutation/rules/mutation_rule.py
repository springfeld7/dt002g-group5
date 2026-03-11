"""mutation_rule.py

Defines the MutationRule abstract base class and the MutationRecord schema.
This module provides the interface for CST mutations and the 
reporting mechanism for tracking changes via original source coordinates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from ..mutation_types import MutationAction
from dataclasses import dataclass
from ..mutation_types import MutationAction, validate_action_metadata
from ...node import Node


@dataclass(frozen=True)
class MutationRecord:
    """
    A record of a single source code transformation.

    Attributes:
        node_id (Tuple[int, int]): The unique coordinate identifier for the target
            node (Original: (row, col) | Synthetic: negative coordinates).
        action (MutationAction): The transformation type applied to the node.
        metadata (Dict[str, Any]): Action-specific data required for verification,
            validated against the action's schema.
    """

    node_id: Tuple[int, int]
    action: MutationAction
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Enforce the mutation contract upon instantiation."""
        validate_action_metadata(self.action, self.metadata)


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

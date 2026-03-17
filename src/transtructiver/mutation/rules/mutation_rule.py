"""mutation_rule.py

Defines the MutationRule abstract base class and the MutationRecord schema.
This module provides the interface for CST mutations and the 
reporting mechanism for tracking changes via original source coordinates.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
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

    Class attribute (optional):
        rule_name (str): The CLI name used to select this rule (e.g. "my-rule").
            If not set, a name is auto-derived from the class name by stripping
            the trailing "Rule" suffix and converting to kebab-case.
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

    # ------------------------------------------------------------------
    # Convenience helpers — used instead of constructing
    # MutationRecord objects manually.
    # ------------------------------------------------------------------

    def iter_by_label(self, root: Node, *labels: str) -> Iterator[Node]:
        """Yield every node in the tree whose semantic_label is in *labels*.

        Example::

            for node in self.iter_by_label(root, "variable_name", "parameter_name"):
                ...
        """
        for node in root.traverse():
            if node.semantic_label in labels:
                yield node

    def record_rename(self, node: Node, new_text: str) -> "MutationRecord":
        """Return a RENAME record and update node.text in one call.

        Args:
            node: The identifier node to rename.
            new_text: The replacement identifier text.

        Returns:
            A MutationRecord ready to append to your records list.
        """
        node.text = new_text
        return MutationRecord(
            node_id=node.start_point,
            action=MutationAction.RENAME,
            metadata={"new_val": new_text},
        )

    def record_reformat(self, node: Node, new_text: str) -> "MutationRecord":
        """Return a REFORMAT record and update node.text in one call.

        Args:
            node: The node whose text should be reformatted.
            new_text: The replacement text.

        Returns:
            A MutationRecord ready to append to your records list.
        """
        node.text = new_text
        return MutationRecord(
            node_id=node.start_point,
            action=MutationAction.REFORMAT,
            metadata={"new_val": new_text},
        )

    def record_insert(
        self, point: tuple[int, int], insertion_point: tuple[int, int], new_text: str, new_type: str
    ) -> "MutationRecord":
        """Insert *node* into *parent* and return an INSERT record.

        Args:
            point: The insert point of the node.
            insertion_point: The point where the node will be inserted in relation to the original
            new_text: The text of the inserted node.
            new_type: The type of the inserted node.

        Returns:
            A MutationRecord ready to append to your records list.
        """
        return MutationRecord(
            node_id=point,
            action=MutationAction.INSERT,
            metadata={
                "new_val": new_text,
                "node_type": new_type,
                "insertion_point": insertion_point,
            },
        )

    def record_delete(self, parent: Node, node: Node) -> "MutationRecord":
        """Remove *node* from *parent* and return a DELETE record.

        Args:
            parent: The direct parent node that owns *node*.
            node: The node to remove from the tree.

        Returns:
            A MutationRecord ready to append to your records list.
        """
        parent.remove_child(node)
        return MutationRecord(
            node_id=node.start_point,
            action=MutationAction.DELETE,
            metadata={"node_type": node.type, "content": node.text},
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the mutation rule.

        Used for debugging and logging to identify the specific rule
        class being applied (e.g., '<ControlFlowFlattening>').
        """
        return f"<{self.name}>"

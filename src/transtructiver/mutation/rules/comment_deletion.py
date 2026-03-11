"""comment_deletion.py

Defines the CommentDeletion mutation rule, which removes all comment nodes
from a Concrete Syntax Tree (CST). Each deletion generates a MutationRecord
capturing the original source coordinates and content of the removed comment.

This module provides a concrete implementation of the MutationRule interface
for comment removal, supporting downstream verification and manifest generation.
"""

from typing import List
from .mutation_rule import MutationRule, MutationRecord
from ..mutation_types import MutationAction
from ...node import Node


class CommentDeletionRule(MutationRule):
    """
    Concrete mutation rule that deletes all comment nodes from a CST.

    Each deletion generates a MutationRecord with the node's original coordinates.
    """

    def apply(self, root: Node) -> List[MutationRecord]:
        """
        Apply the CommentDeletion mutation rule to the CST.

        This method recursively traverses the tree rooted at `root`,
        removes any nodes of type "comment", and returns a list of
        MutationRecords describing each deletion.

        Args:
            root (Node): The root node of the CST to mutate.

        Returns:
            List[MutationRecord]: A list of all deletions performed,
            each containing the original coordinates and text content of the removed comment.
        """
        records: List[MutationRecord] = []

        for child in list(root.children):
            if child.semantic_label == "comment":
                # Remove comment from tree
                root.remove_child(child)

                # Record the mutation
                record = MutationRecord(
                    node_id=child.start_point,
                    action=MutationAction.DELETE,
                    metadata={"node_type": child.type, "content": child.text},
                )
                records.append(record)
            else:
                # Recursively process child nodes
                records.extend(self.apply(child))

        return records

"""insert_strategy.py

Defines the InsertVerificationStrategy for validating node additions.
"""

from typing import List, Optional

from src.transtructiver.mutation.mutation_types import MutationAction
from ...mutation.mutation_manifest import ManifestEntry
from ...node import Node
from .verification_strategy import VerificationStrategy


class InsertVerificationStrategy(VerificationStrategy):
    """
    Validation logic for node addition (INSERT).

    Ensures that new nodes are correctly identified as 'synthetic'
    and do not overlap with real-world source coordinates.
    """

    def verify(self, orig: Optional[Node], mut: Optional[Node], entry: ManifestEntry) -> List[str]:
        """
        Audits an insertion to ensure the new node is officially tracked.

        Args:
            orig (Optional[Node]): Should be None for an insertion.
            mut (Optional[Node]): The newly added node.
            entry (ManifestEntry): The manifest record for the insertion.

        Returns:
            List[str]: Error if coordinates are not synthetic (negative).
        """
        if mut is None:
            return [
                f"Logic Error: InsertVerificationStrategy missing mutated node at {entry.original_id}"
            ]

        # Inserted nodes must have negative line numbers to avoid collision
        if mut.start_point[0] >= 0:
            return [
                f"Logic Error: Inserted node {mut.type} has non-synthetic coordinates at {mut.start_point}"
            ]

        # Authorization Check: Ensure the manifest history contains an INSERT
        if not any(h["action"] == MutationAction.INSERT for h in entry.history):
            last_action = entry.history[-1]["action"]
            return [
                f"Unauthorized insertion: Manifest expected {last_action} for node at {mut.start_point}"
            ]

        return []

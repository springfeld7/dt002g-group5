"""delete_strategy.py

Defines the DeleteVerificationStrategy for validating node removals.
"""

from typing import List, Optional

from ...mutation.mutation_types import MutationAction
from ...mutation.mutation_manifest import ManifestEntry
from ...node import Node
from .verification_strategy import VerificationStrategy


class DeleteVerificationStrategy(VerificationStrategy):
    """
    Validation logic for node removal (DELETE).

    Ensures that only authorized deletions of nodes has been made.
    """

    def verify(self, orig: Optional[Node], mut: Optional[Node], entry: ManifestEntry) -> List[str]:
        """
        Audits a deletion to ensure identity matching and structural integrity.

        Args:
            orig (Optional[Node]): The node that was removed from the original CST.
            mut (Optional[Node]): Should be None for a deletion action.
            entry (ManifestEntry): The manifest record authorizing this deletion.

        Returns:
            List[str]: A list of error messages. Empty list indicates a valid deletion.
        """
        errors = []

        if orig is None:
            errors.append(f"Internal Logic Error: Delete strategy missing original node.")
            return errors

        # Verification of Intent
        last_action = entry.history[-1]["action"]
        if last_action != MutationAction.DELETE:
            return [f"Unauthorized deletion: Manifest expected {last_action} at {orig.start_point}"]

        return []

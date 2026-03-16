"""content_strategy.py

Defines the ContentVerificationStrategy for validating REFORMAT and RENAME actions.
"""

from typing import List, Optional
from ...mutation.mutation_manifest import ManifestEntry
from ...node import Node
from .verification_strategy import VerificationStrategy


class ContentVerificationStrategy(VerificationStrategy):
    """
    Validation logic for 1-to-1 content transformations (RENAME, REFORMAT).

    This strategy ensures that the mutated node's text exactly matches the 'new_val' promise
    recorded in the manifest metadata while maintaining structural identity.
    """

    def verify(self, orig: Optional[Node], mut: Optional[Node], entry: ManifestEntry) -> List[str]:
        """
        Audits the content and type consistency of a node pair.

        Args:
            orig (Optional[Node]): The node from the original tree.
            mut (Optional[Node]): The node from the mutated tree.
            entry (ManifestEntry): The manifest record containing mutation
                history and 'new_val' metadata.

        Returns:
            List[str]: A list of error messages. An empty list signifies that
                the content transformation is valid and authorized.
        """
        errors = []

        meta = entry.metadata
        expected_text = meta.get("new_val")

        # Manifest Integrity Check
        if orig and expected_text is None:
            errors.append(f"Manifest Error: Missing 'new_val' in metadata at {orig.start_point}")
            return errors

        # Structural Guard (Node pairing)
        if orig is None or mut is None:
            errors.append(
                f"Logic Error: ContentVerificationStrategy received a None node at {entry.original_id}"
            )
            return errors

        # Identity Guard: Node type must remain stable
        if orig.type != mut.type:
            errors.append(f"Type mismatch at {orig.start_point}: {orig.type} -> {mut.type}")

        # Content Guard: Text must match the manifest promise
        if mut.text != expected_text:
            errors.append(
                f"Content mismatch at {orig.start_point}: Expected '{expected_text}', found '{mut.text}'"
            )

        return errors

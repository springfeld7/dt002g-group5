"""verification_strategy.py
Defines the VerificationStrategy ABC for validating specific mutation actions.
This module provides a structured interface for implementing various verification
strategies corresponding to different MutationActions. Each strategy encapsulates
the logic required to audit a particular type of transformation, ensuring that the
mutated CST adheres to the structural and content constraints defined in the manifest.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.transtructiver.mutation.mutation_manifest import ManifestEntry
from ...node import Node


class VerificationStrategy(ABC):
    """
    Abstract Base Class for all Semantic Isomorphism (SI) verification logic.

    Each concrete strategy encapsulates the validation rules for a specific MutationAction.
    """

    @abstractmethod
    def verify(self, orig: Optional[Node], mut: Optional[Node], entry: ManifestEntry) -> List[str]:
        """
        Audits a node pair (or single node) against the manifest contract.

        Args:
            orig: The node from the original tree (None for INSERT).
            mut: The node from the mutated tree (None for DELETE).
            entry: The manifest entry containing the node's history and mutation metadata.

        Returns:
            List[str]: A list of error messages. Empty list indicates success.
        """
        pass

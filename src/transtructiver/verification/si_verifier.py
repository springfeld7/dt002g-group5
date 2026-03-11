"""si_verifier.py

This module implements the Structural Integrity Verifier (SIVerifier).
It validates Semantic Isomorphism (SI) by ensuring that every transformation 
found in a mutated CST is authorized and documented within a MutationManifest.
"""

import csv
import os
from typing import List, Optional
from ..mutation.mutation_manifest import MutationManifest, ManifestEntry
from ..mutation.mutation_types import MutationAction
from ..node import Node
from .strategies.registry import STRATEGY_MAP


class SIVerifier:
    """
    The authoritative engine for verifying Semantic Isomorphism (SI).

    The SIVerifier performs a synchronized recursive traversal of two trees
    to ensure that the mutated tree remains a semantic mirror of the original.
    It enforces strict identity across node types, text, attributes, and
    coordinates, except where specific deviations are authorized by a
    MutationAction contract in the manifest.

    Attributes:
        strategies (dict): A mapping of MutationActions to their corresponding
            VerificationStrategy instances. This allows for dynamic dispatch of
            validation logic based on the type of transformation recorded in the manifest.
        errors (list[str]): A collection of semantic and structural discrepancies
            found during verification. This list is reset at the start of each verify() call.
    """

    def __init__(self):
        self.strategies = STRATEGY_MAP
        self.errors: List[str] = []

    def _report(self, msg: str) -> None:
        """Logs a discrepancy."""
        self.errors.append(msg)

    def verify(self, original_tree: Node, mutated_tree: Node, manifest: MutationManifest) -> bool:
        """
        Entry point for the recursive Semantic Isomorphism (SI) audit.

        If the manifest indicates that structural changes were made, the verifier performs
        a synchronized traversal to validate each node against the manifest's transformation contract.
        If no structural changes are present, a fast zipper-based check is performed to confirm strict identity.

        Args:
            original_tree (Node): The root node of the source CST before mutation.
            mutated_tree (Node): The root node of the in-memory CST after mutation.
            manifest (MutationManifest): The record of all authorized changes
                (actions, metadata, and coordinates) performed during the session.

        Returns:
            bool: True if the mutated tree is a perfect, authorized projection of
                the original; False if any unauthorized drift or structural
                misalignment was detected.
        """
        self.errors = []  # Reset error log
        self._halt = False  # Reset circuit breaker

        if manifest.has_structural_changes():
            return self._verify_synchronized(original_tree, mutated_tree, manifest)

        return self._verify_aligned(original_tree, mutated_tree, manifest)

    def _verify_aligned(self, orig: Node, mut: Node, manifest: MutationManifest) -> bool:
        """
        Performs a high-speed, 1-to-1 recursive traversal of two trees.

        Returns:
            bool: True if the branch is isomorphic/valid; False if any
                  discrepancy is found (halts further traversal).
        """
        # Validate the current node pair
        if not self._apply_node_strategy(orig, mut, manifest):
            return False

        # Structural check: Circuit breaker for unexpected topological drift
        if len(orig.children) != len(mut.children):
            self._report(f"Structural discrepancy at {orig.start_point}: child count mismatch.")
            return False

        # Recurse: Check all children. If any child returns False, halt immediately
        for o_child, m_child in zip(orig.children, mut.children):
            if not self._verify_aligned(o_child, m_child, manifest):
                return False

        return True

    def _verify_synchronized(self, orig: Node, mut: Node, manifest: MutationManifest) -> bool:
        """
        Performs a gap-aware traversal to handle non-isomorphic tree topologies.

        Uses an iterator-based lookahead to synchronize the original and mutated
        trees. It handles authorized deletions by skipping nodes in the original
        tree and accounts for synthetic nodes by validating them against
        insertion entries in the manifest.

        Args:
            orig (Node): Current node from the original CST.
            mut (Node): Current node from the mutated CST.
            manifest (MutationManifest): The record of authorized transformations.

        Returns:
            bool: True if the entire subtree is valid and authorized; False
                immediately upon detecting any unauthorized drift.
        """
        # Validate current node pair
        if not self._apply_node_strategy(orig, mut, manifest):
            return False

        orig_iter = iter(orig.children)
        mut_children = mut.children
        m_idx = 0

        while m_idx < len(mut_children):
            m_child = mut_children[m_idx]

            # Handle INSERTED Nodes (Lookahead in Mutated Tree)
            if m_child.start_point[0] < 0:  # Synthetic nodes have negative row numbers
                if not self._apply_node_strategy(None, m_child, manifest):
                    return False
                m_idx += 1
                continue

            # Handle DELETED/EXISTING Nodes (Lookahead in Original Tree)
            try:
                o_child = next(orig_iter)

                # Advance orig_iter to skip authorized deletions
                while self._is_deleted(o_child, manifest):
                    if not self._apply_node_strategy(o_child, None, manifest):
                        return False
                    o_child = next(orig_iter)

                # Trees are now aligned; recurse into children
                if not self._verify_synchronized(o_child, m_child, manifest):
                    return False
                m_idx += 1

            except StopIteration:
                # The mutated tree is providing a node that 'should' have an original
                # counterpart, but we've already exhausted the original child list.
                self._report(f"Unexpected node {m_child.type} at {m_child.start_point}")
                return False

        # Ensure every node remaining in the original iterator was
        # explicitly authorized for removal/transformation in the manifest.
        for leftover in orig_iter:
            if not self._is_deleted(leftover, manifest):
                self._report(f"Missing non-deleted node: {leftover.type} at {leftover.start_point}")
                return False

        return True

    def _apply_node_strategy(
        self, orig: Optional[Node], mut: Optional[Node], manifest: MutationManifest
    ) -> bool:
        """
        Delegates validation for a node pair to a specialized VerificationStrategy.

        This method acts as the primary decision engine for node-level isomorphism.
        If no manifest entry exists, it performs a strict identity check. If an
        entry exists, it dispatches validation to the strategy corresponding to
        the last recorded MutationAction.

        Args:
            orig (Optional[Node]): The node from the original tree, or None if INSERTED.
            mut (Optional[Node]): The node from the mutated tree, or None if DELETED.
            manifest (MutationManifest): The central mutation registry.

        Returns:
            bool: True if the node pair complies with the manifest or identity
                rules; False if an unauthorized change is detected, signaling
                the walker to cease all further traversal.
        """
        # Determine the source of truth for the manifest lookup.
        # Original coordinates are the primary keys.
        point = orig.start_point if orig else mut.start_point
        entry = manifest.get_entry(point)

        if entry is None:
            # IDENTITY CHECK: No mutation recorded, must be a perfect mirror
            if not self._verify_identity(orig, mut):
                self._report(f"Unauthorized change at {point}")
                return False
            return True

        # STRATEGY DISPATCH
        # Should be alright for now, as we only do one action but not sure what will happen
        # when we have multiple actions on the same node when FLATTEN or SUBSTITUTE come into play.
        # For now it is even redudant to take the last action because there should only be one action per node.
        action = entry.history[-1]["action"]
        strategy = self.strategies.get(action)

        if not strategy:
            self._report(f"No strategy found for action: {action} at {point}")
            return False

        self.errors.extend(strategy.verify(orig, mut, entry))

        return len(self.errors) == 0

    def _is_deleted(self, node: Node, manifest: MutationManifest) -> bool:
        """
        Helper to determine if an original node was marked for deletion.

        Args:
            node (Node): The node in the original tree to check.
            manifest (MutationManifest): The central mutation registry.

        Returns:
            bool: True if the manifest contains a DELETE action for this node.
        """
        entry = manifest.get_entry(node.start_point)
        return entry is not None and any(
            h["action"] == MutationAction.DELETE for h in entry.history
        )

    def _verify_identity(self, orig: Node, mut: Node) -> bool:
        """
        Pure check for strict structural and content identity between two nodes.
        Returns True if identical, False otherwise.
        """
        return (
            orig.type == mut.type
            and orig.text == mut.text
            and orig.start_point == mut.start_point
            and orig.end_point == mut.end_point
        )

    def write_summary(self, snippet_id: str, verified: bool, log_path: str = "summary_log.csv"):
        """
        Records the outcome of a verification run to a specified CSV log.

        This method facilitates both production auditing and isolated testing
        by allowing the caller to specify the destination file.

        Args:
            snippet_id (str): Unique identifier for the snippet.
            verified (bool): The success status of the isomorphism check.
            log_path (str): The destination file path. Defaults to 'summary_log.csv'
                for standard production runs.

        Note:
            - The file is opened in 'append' mode.
            - If the path provided by a test (e.g., via tmp_path) does not exist,
              Python will create it automatically upon the first write.
        """
        status = 1 if verified else 0
        reason = (
            "" if verified else (" | ".join(self.errors) if self.errors else "Unknown Mismatch")
        )

        # Ensure the directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError as e:
                print(f"CRITICAL: Could not create log directory {log_dir}: {e}")
                return

        try:
            with open(log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([snippet_id, status, reason])
        except (PermissionError, IOError) as e:
            print(f"ERROR: Failed to write to {log_path}: {e}")

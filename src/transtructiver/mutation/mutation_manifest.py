"""mutation_manifest.py

This module contains the registry and data structures for tracking node transformations.
It provides a centralized audit trail to ensure data integrity during complex, 
multi-pass mutation processes.

Key Components:
    * MutationManifest: The primary registry (container) that manages all entries.
    * ManifestEntry: The individual record for a specific node, tracking its 
      metadata, history, and structural state.
"""

import copy
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from .mutation_types import MutationAction


@dataclass
class ManifestEntry:
    """
    A single record within the MutationManifest representing a specific node's history and state.

    This class serves as the 'source of truth' for an individual node (keyed by its
    original_id). It stores the cumulative result of all transformations,
    maintaining an audit trail of changes and ensuring that structural
    mutations remain consistent and conflict-free.

    Attributes:
        original_id (Tuple[int, int]): The source identifier (e.g., line/column).
        history (List[Dict[str, MutationAction]]): A chronological log of rule names and actions applied to this node.
        metadata (Dict[str, Any]): Cumulative key-value pairs describing mutations and their parameters.
    """

    original_id: Tuple[int, int]
    history: List[Dict[str, MutationAction]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, metadata: Dict[str, Any], rule_name: str, action: MutationAction) -> None:
        """
        Integrates a new mutation into the existing entry.

        Appends the rule to the audit trail and merges the given metadata into the entry.

        Args:
            metadata: Dictionary of new attributes to merge.
            rule_name: Name of the rule responsible for this change.
            action: The MutationAction being applied.
        """
        self.history.append({"rule": rule_name, "action": action})
        # Use deepcopy to prevent external changes from affecting the manifest
        safe_metadata = copy.deepcopy(metadata)
        self.metadata.update(safe_metadata)


class MutationManifest:
    """
    The central registry for all node mutations across a transformation pass.

    This class serves as a lookup table to ensure that disparate transformation
    rules can stay synchronized and avoid redundant or conflicting changes
    to the same data nodes.

    Attributes:
        _entries (Dict[Tuple[int, int], ManifestEntry]): Maps original node IDs to their mutation records.
        _has_structural (bool): Flag indicating if any structural mutations have been recorded.
    """

    def __init__(self):
        """Initializes the manifest with an empty registry."""
        self._entries: Dict[Tuple[int, int], ManifestEntry] = {}
        self._has_structural_changes = False

    def add_entry(
        self,
        node_id: Tuple[int, int],
        action: MutationAction,
        metadata: Dict[str, Any],
        rule_name: str,
    ) -> None:
        """
        Registers a mutation for a specific node ID.

        If the node_id does not exist in the manifest, a new ManifestEntry
        is created. Otherwise, the existing entry is updated.

        Args:
            node_id: The (row, col) or unique ID of the node to mutate.
            metadata: Data associated with this specific mutation step.
            rule_name: The name of the logic/rule triggering the update.
            action: The MutationAction being applied.
        """
        if node_id not in self._entries:
            self._entries[node_id] = ManifestEntry(original_id=node_id)

        if action is not None and action.is_structural:
            self._has_structural_changes = True

        entry = self._entries[node_id]
        entry.update(metadata, rule_name, action)

    def get_entry(self, node_id: Tuple[int, int]) -> Optional[ManifestEntry]:
        """
        Retrieves the ManifestEntry for a node, if it exists.

        Args:
            node_id: The ID of the node to look up.

        Returns:
            The associated ManifestEntry object or None if no mutations recorded.
        """
        return self._entries.get(node_id)

    def has_structural_changes(self) -> bool:
        """
        Queries the manifest to determine if any topology-altering mutations
        have been recorded.

        Returns:
            bool: True if at least one action with 'is_structural = True'
                (e.g., INSERT, DELETE, FLATTEN, SUBSTITUTE) has been
                added to the manifest; False otherwise.
        """
        return self._has_structural_changes

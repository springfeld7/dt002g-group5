"""mutation_engine.py

The MutationEngine manages the transformation lifecycle by sequentially applying rules 
and recording every change in a centralized MutationManifest. This provides 
a verifiable history of how each node in the tree was modified.
"""

from typing import List
from .rules.mutation_rule import MutationRecord, MutationRule
from .mutation_manifest import MutationManifest
from .mutation_context import MutationContext
from ..node import Node


class MutationEngine:
    """
    Engine for applying mutation rules to transform syntax trees.

    The MutationEngine takes a list of mutation rules and applies them sequentially
    to a CST. It aggregates local changes into a global MutationManifest keyed
    by the original source coordinates of the nodes.

    Attributes:
        rules (List[MutationRule]): Sequence of rules to be executed.
    """

    def __init__(self, rules: List[MutationRule]):
        """
        Initialize the MutationEngine with a list of rules.

        Args:
            rules (List[MutationRule]): List of mutation rule objects.
        """
        self.rules: List[MutationRule] = rules
        self.manifest: MutationManifest = MutationManifest()

    def apply_mutations(self, cst: Node) -> MutationManifest:
        """
        Apply all mutation rules to the given CST.

        Rules are applied sequentially. This method populates the transformation Manifest
        by aggregating mutation records from each rule, which serves as the
        source of truth for downstream verification. The result is also stored
        as ``self.manifest`` for post-hoc inspection by the caller.

        Args:
            cst (Node): The root node of the CST to mutate.

        Returns:
            MutationManifest: The complete transformation Manifest.
        """
        manifest = MutationManifest()
        context = MutationContext()

        # Ensure that WhitespaceNormalizationRule runs first
        # to ensure DeadCodeInsertionRule relies upon consistent indentation
        self.rules.sort(key=lambda r: 0 if r.rule_name == "whitespace-normalization" else 1)

        for rule in self.rules:
            local_changes = rule.apply(cst, context)
            self._merge_to_manifest(manifest, local_changes, rule.name)

        self.manifest = manifest
        return manifest

    def _merge_to_manifest(
        self, manifest: MutationManifest, changes: List[MutationRecord], rule_name: str
    ) -> None:
        """
        Converts MutationRecords into ManifestEntries and merges them into
        a mutation manifest.

        Args:
            manifest: The mutation manifest to merge changes into.
            changes: A list of mutations produced by a single rule execution.
            rule_name: The name of the rule, used for audit history.
        """
        for record in changes:
            manifest.add_entry(
                node_id=record.node_id,
                action=record.action,
                metadata=record.metadata,
                rule_name=rule_name,
            )

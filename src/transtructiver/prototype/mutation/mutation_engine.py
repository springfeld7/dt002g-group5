"""Mutation Engine for applying transformation rules to Concrete Syntax Trees (CST).

The MutationEngine orchestrates the application of one or more mutation rules to a CST,
allowing systematic transformation and modification of code structure.
"""


class MutationEngine:
    """Engine for applying mutation rules to transform syntax trees.

    The MutationEngine takes a list of mutation rules and applies them sequentially
    to a Concrete Syntax Tree (CST). Each rule transforms the tree in place.

    Attributes:
        rules (list): List of mutation rules to apply. Each rule must have an apply() method.
    """

    def __init__(self, rules):
        """Initialize the MutationEngine with a list of rules.

        Args:
            rules (list): List of mutation rule objects. Each rule should implement
                an apply(node) method that transforms the node and its children.
        """
        self.rules = rules

    def applyMutations(self, cst: Node) -> Dict[Tuple[int, int], ManifestEntry]:
        """Apply all mutation rules to the given CST in-place.

        Rules are applied sequentially. This method populates the Master Manifest
        by aggregating change records from each rule, which serves as the
        source of truth for downstream verification.

        Args:
            cst (Node): The root node of the CST to mutate.

        Returns:
            Dict[Tuple[int, int], ManifestEntry]: The complete Master Manifest.
        """
        for rule in self.rules:
            # The rule modifies the 'cst' object in memory
            local_changes = rule.apply(cst)
            self._merge_to_manifest(local_changes, rule.name)

        return self.manifest

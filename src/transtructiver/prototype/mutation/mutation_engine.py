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
    
    def applyMutations(self, cst):
        """Apply all mutation rules to the given CST.
        
        Rules are applied sequentially. The output of one rule becomes the input
        to the next rule. This allows for composable transformations.
        
        Args:
            cst (Node): The root node of the Concrete Syntax Tree to mutate.
        
        Returns:
            Node: The transformed syntax tree after all rules have been applied.
        
        Example:
            >>> engine = MutationEngine([RenameIdentifiersRule()])
            >>> mutated_tree = engine.applyMutations(original_tree)
        """
        for rule in self.rules:
            cst = rule.apply(cst)
        return cst

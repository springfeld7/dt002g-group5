"""Mutation rules for transforming Abstract/Concrete Syntax Trees.

This module defines concrete mutation rules that can be applied to transform
syntax trees. Each rule implements a specific transformation strategy.
"""


class RenameIdentifiersRule:
    """A mutation rule that renames all identifiers in the tree.

    This rule applies a prefix "x_" to all identifier nodes in a syntax tree.
    It recursively traverses the tree and modifies each identifier's text.

    Example:
        Before: Node(type='identifier', text='add')
        After:  Node(type='identifier', text='x_add')
    """

    def apply(self, node):
        """Apply the rename transformation to an identifier node and its descendants.

        This method recursively traverses the syntax tree and prefixes all identifier
        nodes with "x_". Non-identifier nodes are passed through unchanged but their
        children are still processed.

        Args:
            node (Node): The root node to transform. Can be any node type.

        Returns:
            Node: The same node with identifiers renamed (modified in place).

        Example:
            >>> rule = RenameIdentifiersRule()
            >>> tree = Node('identifier', text='x')
            >>> result = rule.apply(tree)
            >>> result.text
            'x_x'
        """
        if node.type == "identifier" and node.text is not None:
            node.text = "x_" + node.text

        for child in node.children:
            self.apply(child)

        return node

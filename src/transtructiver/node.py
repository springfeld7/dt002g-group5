"""
Core node structure for representing Abstract and Concrete Syntax Trees.

This module defines the fundamental Node class used throughout the project
to represent hierarchical code structures.
"""

from typing import Iterator, List, Optional


class Node:
    """
    Represents a node in an Abstract Syntax Tree (AST) or Concrete Syntax Tree (CST).

    A Node is a fundamental building block for representing program structure as a tree.
    Each node has a type (e.g., "identifier", "binary_expression"), optional child nodes,
    and optional text content (for leaf nodes like tokens).

    Attributes:
        type (str): The node type/category (e.g., "identifier", "function_definition").
        children (list): List of child Node objects. Represents the structure of the tree.
        text (str, optional): The raw token text for leaf nodes. None for non-leaf nodes.
    """

    def __init__(
        self,
        type: str,
        children: Optional[List[Node]] = None,
        text: Optional[str] = None,
        is_named: bool = False,
    ) -> None:
        """
        Initialize a new Node.

        Args:
            type (str): The node type/category identifier.
            children (list, optional): List of child Node objects. Defaults to empty list if None.
            text (str, optional): Raw token text for leaf nodes. Defaults to None.
            is_named (bool, optional): Whether the node is a named node. Defaults to False.
        """
        self.type: str = type
        self.children: List[Node] = children or []
        self.text: Optional[str] = text
        self.is_named: bool = is_named

    def add_child(self, child: Node) -> None:
        """
        Add a child node to this node.

        Args:
            child (Node): The child node to add.
        """
        self.children.append(child)

    def traverse(self) -> Iterator[Node]:
        """
        Yield all nodes in the tree using preorder traversal.

        Preorder traversal visits the current node before visiting its children.
        This is useful for visiting nodes in a top-down order.

        Yields:
            Node: Each node in the tree in preorder sequence.
        """
        yield self
        for child in self.children:
            yield from child.traverse()

    def clone(self) -> Node:
        """
        Creates a deep copy of the current node and all its children.

        Returns:
            Node: A new instance of Node with identical type, text, and
                recursively cloned children.
        """
        new_node = Node(self.type, text=self.text)
        new_node.children = [child.clone() for child in self.children]

        return new_node

    def __repr__(self) -> str:
        """
        Return a string representation of the node.

        Returns:
            str: A string showing the node type and text (if present).
        """
        return f"Node(type={self.type}, text={self.text})"

    def pretty(self, indent: int = 0) -> None:
        """
        Print a human-readable tree representation of this node and its children.

        This method recursively prints the tree structure with proper indentation.
        Each level of nesting is indented by 2 spaces.

        Args:
            indent (int, optional): Current indentation level. Defaults to 0 (root level).
                Used internally for recursive calls.

        Example:
            >>> node = Node("function_definition", text="add")
            >>> node.pretty()
            function_definition: add
        """
        prefix = "  " * indent
        line = f"{prefix}{self.type}"

        if self.text is not None and self.is_named:
            line += f": {self.text}"

        print(line)

        for child in self.children:
            child.pretty(indent + 1)

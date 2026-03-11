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
    """

    def __init__(
        self,
        start_point: tuple[int, int],
        end_point: tuple[int, int],
        type: str,
        text: Optional[str] = None,
        children: Optional[List[Node]] = None,
    ) -> None:
        """
        Initialize a new Node.

        Args:
            start_point (tuple[int, int]): Starting position as (row, column).
            end_point (tuple[int, int]): Ending position as (row, column).
            type (str): The node type/category identifier.
            text (str, optional): Raw token text for leaf nodes. Defaults to None.
            children (list, optional): List of child Node objects. Defaults to empty list if None.
        """
        self.start_point = start_point
        self.end_point = end_point
        self.type = type
        self.text = text
        self.children = children or []
        # Links populated during adaptation and annotation for tree navigation.
        self.parent: Optional[Node] = None
        self.semantic_label: Optional[str] = None
        self.field: Optional[str] = None

    def add_child(self, child: Node) -> None:
        """
        Add a child node to this node.

        Args:
            child (Node): The child node to add.
        """
        self.children.append(child)

    def remove_child(self, child: Node) -> None:
        """
        Remove a child node from this node.

        Args:
            child (Node): The child node to remove.

        Raises:
            ValueError: If the node is not a child of this node.
        """
        self.children.remove(child)

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
        new_node = Node(
            self.start_point,
            self.end_point,
            self.type,
            self.text,
        )
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

        Example:
            >>> node = Node("function_definition", text="add")
            >>> node.pretty()
            function_definition: add
        """
        prefix = "  " * indent
        if (self.type != "newline") and (self.type != "whitespace"):
            if self.field:
                line = f"{prefix}('{self.field}') {self.type}"
            else:
                line = f"{prefix}{self.type}"

            if self.text:
                line += f": {self.text}"

            print(line)

        for child in self.children:
            child.pretty(indent + 1)

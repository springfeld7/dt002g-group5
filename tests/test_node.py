"""
Unit tests for the Node class.

This module tests:
- Correct initialization of nodes with type, text, and children.
- Adding children to a node after creation.
- Preorder traversal of nodes.
- Deep-copy behavior via clone().
- Edge cases such as nodes with multiple children and single-node traversal.

Tests cover both typical usage and boundary conditions to ensure
the Node class reliably supports tree construction and manipulation.
"""

import pytest
from src.transtructiver.node import Node


def test_node_initialization():
    """Verify that a node correctly stores type, text, and children."""
    node = Node((0, 0), (0, 1), "identifier", text="x")

    assert node.start_point == (0, 0)
    assert node.end_point == (0, 1)
    assert node.type == "identifier"
    assert node.text == "x"
    assert node.children == []


def test_add_child():
    """Verify that children are correctly appended to the children list."""
    root = Node((0, 0), (0, 1), "binary_expression")
    child = Node((0, 1), (0, 2), "number", text="5")

    root.add_child(child)

    assert len(root.children) == 1
    assert root.children[0].type == "number"
    assert root.children[0].text == "5"


def test_remove_child_removes_existing_child():
    """
    Verify that remove_child correctly removes a child node.

    The method should remove the specified child from the parent's
    children list while leaving other children unchanged.
    """
    parent = Node((0, 0), (0, 0), "parent")

    child1 = Node((1, 0), (1, 1), "child1")
    child2 = Node((2, 0), (2, 1), "child2")

    parent.add_child(child1)
    parent.add_child(child2)

    parent.remove_child(child1)

    assert parent.children == [child2]


def test_remove_child_from_single_child_parent():
    """
    Verify that removing the only child leaves the parent with
    an empty children list.
    """
    parent = Node((0, 0), (0, 0), "parent")
    child = Node((1, 0), (1, 1), "child")

    parent.add_child(child)
    parent.remove_child(child)

    assert parent.children == []


def test_remove_child_raises_error_for_non_child():
    """
    Verify that remove_child raises ValueError when the node
    is not a child of the parent.
    """
    parent = Node((0, 0), (0, 0), "parent")

    child = Node((1, 0), (1, 1), "child")
    other = Node((2, 0), (2, 1), "other")

    parent.add_child(child)

    with pytest.raises(ValueError):
        parent.remove_child(other)


def test_traverse_preorder():
    """Verify preorder traversal: Root -> Left Child -> Left Child's Children -> Right Child."""
    # Build: root(A) -> [child(B), child(C) -> [grandchild(D)]]
    point = (0, 0)
    root = Node(point, point, "A")
    child_b = Node(point, point, "B")
    child_c = Node(point, point, "C")
    grandchild_d = Node(point, point, "D")

    root.add_child(child_b)
    root.add_child(child_c)
    child_c.add_child(grandchild_d)

    # Expected order: A, B, C, D
    traversed_types = [node.type for node in root.traverse()]
    assert traversed_types == ["A", "B", "C", "D"]


def test_clone_deep_copy():
    """Verify that cloning creates a deep copy, not a shallow reference."""
    point = (0, 0)
    root = Node(point, point, "root")
    child = Node(point, point, "child", "original")
    root.add_child(child)

    cloned_root = root.clone()

    # Check values match
    assert cloned_root.type == root.type
    assert cloned_root.children[0].text == "original"

    # Verify they are different objects
    assert cloned_root is not root
    assert cloned_root.children[0] is not root.children[0]

    # Modify clone and ensure original is untouched
    cloned_root.children[0].text = "modified"
    assert root.children[0].text == "original"


def test_clone_preserves_parent_relationships():
    """
    Verify that clone() reconstructs correct parent pointers
    within the cloned tree rather than referencing the original nodes.
    """
    point = (0, 0)

    # Build tree: root -> child -> grandchild
    root = Node(point, point, "root")
    child = Node(point, point, "child")
    grandchild = Node(point, point, "grandchild")

    root.add_child(child)
    child.add_child(grandchild)

    cloned_root = root.clone()

    cloned_child = cloned_root.children[0]
    cloned_grandchild = cloned_child.children[0]

    # Root should have no parent
    assert cloned_root.parent is None

    # Parent relationships should point within the cloned tree
    assert cloned_child.parent is cloned_root
    assert cloned_grandchild.parent is cloned_child

    # Ensure they do NOT point to original nodes
    assert cloned_child.parent is not root
    assert cloned_grandchild.parent is not child


def test_node_with_multiple_children_init():
    """Verify initializing a node with a pre-defined list of children."""
    point = (0, 0)
    children = [Node(point, point, "int", "1"), Node(point, point, "int", "2")]

    root = Node(point, point, "list", children=children)

    assert len(root.children) == 2
    assert root.children[0].text == "1"
    assert root.children[1].text == "2"


def test_traverse_single_node():
    """Ensure traversal works even if there are no children."""
    node = Node((0, 0), (0, 0), "leaf")

    result = list(node.traverse())

    assert len(result) == 1
    assert result[0].type == "leaf"

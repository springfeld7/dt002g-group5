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

from transtructiver.node import Node


def test_node_initialization():
    """
    Verify that a node correctly stores type, text, and children.
    """
    node = Node("identifier", text="x")

    assert node.type == "identifier"
    assert node.text == "x"
    assert node.children == []


def test_add_child():
    """
    Verify that children are correctly appended to the children list.
    """
    root = Node("binary_expression")
    child = Node("number", text="5")

    root.add_child(child)

    assert len(root.children) == 1
    assert root.children[0].type == "number"
    assert root.children[0].text == "5"


def test_traverse_preorder():
    """
    Verify preorder traversal: Root -> Left Child -> Left Child's Children -> Right Child.
    """
    # Build: root(A) -> [child(B), child(C) -> [grandchild(D)]]
    root = Node("A")
    child_b = Node("B")
    child_c = Node("C")
    grandchild_d = Node("D")

    root.add_child(child_b)
    root.add_child(child_c)
    child_c.add_child(grandchild_d)

    # Expected order: A, B, C, D
    traversed_types = [node.type for node in root.traverse()]
    assert traversed_types == ["A", "B", "C", "D"]


def test_clone_deep_copy():
    """
    Verify that cloning creates a deep copy, not a shallow reference.
    """
    root = Node("root")
    child = Node("child", text="original")
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


def test_node_with_multiple_children_init():
    """
    Verify initializing a node with a pre-defined list of children.
    """
    children = [Node("int", text="1"), Node("int", text="2")]

    root = Node("list", children=children)

    assert len(root.children) == 2
    assert root.children[0].text == "1"
    assert root.children[1].text == "2"


def test_traverse_single_node():
    """
    Ensure traversal works even if there are no children.
    """
    node = Node("leaf")

    result = list(node.traverse())

    assert len(result) == 1
    assert result[0].type == "leaf"

"""Unit tests for comment_deletion.py

Validates that the CommentDeletion mutation rule correctly removes
comment nodes from a CST, generates MutationRecords for each deletion,
and preserves non-comment nodes.
"""

import pytest
from src.transtructiver.mutation.rules.comment_deletion import CommentDeletionRule
from src.transtructiver.mutation.rules.mutation_rule import MutationRecord
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.node import Node


# ===== Helpers =====


def make_tree_with_comments():
    """Return a CST with top-level and nested comment nodes for testing."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 5), "comment", text="// header comment"),
            Node((1, 0), (1, 3), "identifier", text="x"),
            Node(
                (2, 0),
                (2, 0),
                "block",
                children=[
                    Node((2, 0), (2, 5), "comment", text="// inside block"),
                    Node((3, 0), (3, 3), "identifier", text="y"),
                ],
            ),
        ],
    )


def make_tree_with_only_comments():
    """Return a CST containing only comment nodes."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 5), "comment", text="// a"),
            Node((1, 0), (1, 5), "comment", text="// b"),
        ],
    )


def make_tree_without_comments():
    """Return a CST with no comment nodes."""
    return Node((0, 0), (0, 0), "program", children=[Node((1, 0), (1, 3), "identifier", text="x")])


def label_comments(root: Node) -> Node:
    """
    Traverse the tree and set semantic_label='comment' for all nodes
    whose type is 'comment'.

    Args:
        root (Node): Root of the CST.

    Returns:
        Node: The same root with comment nodes labeled.
    """
    for node in root.traverse():
        if node.type == "comment":
            node.semantic_label = "comment"
    return root


def collect_node_types(root: Node):
    """Return a list of all node types in the tree (preorder traversal)."""
    return [node.type for node in root.traverse()]


# ===== Fixtures =====


@pytest.fixture
def comment_rule():
    """Fixture providing a reusable CommentDeletion instance."""
    return CommentDeletionRule()


@pytest.fixture
def sample_tree():
    """Fresh CST with comments for testing."""
    return label_comments(make_tree_with_comments())


@pytest.fixture
def comments_only_tree():
    """CST containing only comment nodes."""
    return label_comments(make_tree_with_only_comments())


@pytest.fixture
def no_comments_tree():
    """CST containing no comment nodes."""
    return make_tree_without_comments()


# ===== Positive Cases =====


def test_comment_nodes_removed(sample_tree, comment_rule):
    """Verify that all comment nodes are removed from the CST."""
    _ = comment_rule.apply(sample_tree)

    assert "comment" not in collect_node_types(sample_tree)


def test_non_comment_nodes_preserved(sample_tree, comment_rule):
    """Verify that non-comment nodes remain intact after deletion."""
    _ = comment_rule.apply(sample_tree)
    types = collect_node_types(sample_tree)

    assert "program" in types
    assert "identifier" in types
    assert "block" in types


def test_mutation_records_for_comments(sample_tree, comment_rule):
    """Verify that MutationRecords are created for each deleted comment node."""
    records = comment_rule.apply(sample_tree)

    assert len(records) == 2
    for rec in records:
        assert isinstance(rec, MutationRecord)
        assert rec.action == MutationAction.DELETE
        assert rec.metadata["node_type"] == "comment"
        assert rec.metadata["content"].startswith("//")


def test_nested_comments_deleted(sample_tree, comment_rule):
    """Verify that comments nested inside blocks are removed."""
    _ = comment_rule.apply(sample_tree)

    assert all(n.type != "comment" for n in sample_tree.traverse())


# ===== Edge Cases =====


def test_all_comments_deleted_only(comments_only_tree, comment_rule):
    """Verify a tree with only comments ends up empty and returns all MutationRecords."""
    records = comment_rule.apply(comments_only_tree)

    assert comments_only_tree.children == []
    assert len(records) == 2
    for rec in records:
        assert rec.metadata["node_type"] == "comment"


def test_tree_with_no_comments_returns_empty_records(no_comments_tree, comment_rule):
    """Verify a tree without comments returns an empty list and remains unchanged."""
    records = comment_rule.apply(no_comments_tree)

    assert records == []
    assert len(no_comments_tree.children) == 1
    assert no_comments_tree.children[0].type == "identifier"


def test_empty_tree_returns_no_records(comment_rule):
    """Verify applying CommentDeletion to an empty tree returns empty records."""
    root = Node((0, 0), (0, 0), "program")

    records = comment_rule.apply(root)

    assert records == []
    assert root.children == []

"""Unit tests for comment_normalization.py

Validates that the CommentNormalizationRule correctly identifies comment nodes,
normalizes their content to a fixed placeholder (........), and handles
both flat (leaf) and nested (docstring) CST topologies.
"""

import pytest
from src.transtructiver.mutation.rules.comment_normalization import CommentNormalizationRule
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.mutation.mutation_context import MutationContext
from src.transtructiver.node import Node


# ===== Helpers =====


def make_flat_tree():
    """Return a CST with flat line/block comments (C++, Java, #)."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 10), "line_comment", text="// old comment"),
            Node((1, 0), (1, 15), "block_comment", text="/* old block */"),
        ],
    )


def make_nested_tree():
    """Return a CST with a Python-style nested docstring."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node(
                (0, 0),
                (0, 10),
                "block_comment",
                children=[
                    Node((0, 0), (0, 3), "string_start", text='"""'),
                    Node((0, 3), (0, 8), "string_content", text=" doc "),
                    Node((0, 8), (0, 11), "string_end", text='"""'),
                ],
            )
        ],
    )


def label_comments(root: Node, label: str) -> Node:
    """Helper to label nodes based on expected semantic_label."""
    for node in root.traverse():
        if node.type in ["line_comment", "block_comment"]:
            node.semantic_label = label
    return root


# ===== Fixtures =====


@pytest.fixture
def normalization_rule():
    return CommentNormalizationRule()


@pytest.fixture
def flat_tree():
    tree = make_flat_tree()
    label_comments(tree, "line_comment")
    # Manually fix specific semantic labels for this test setup
    for n in tree.children:
        if n.type == "line_comment":
            n.semantic_label = "line_comment"
        if n.type == "block_comment":
            n.semantic_label = "block_comment"
    return tree


@pytest.fixture
def nested_tree():
    tree = make_nested_tree()
    tree.children[0].semantic_label = "block_comment"
    return tree


@pytest.fixture
def mutation_context():
    """Return a default MutationContext for testing."""
    return MutationContext()


# ===== Positive Cases =====


def test_flat_comments_normalized(flat_tree, normalization_rule, mutation_context):
    """Verify flat comments are replaced with the FILLER."""
    records = normalization_rule.apply(flat_tree, mutation_context)

    assert len(records) == 2
    assert flat_tree.children[0].text == "//........"
    assert flat_tree.children[1].text == "/*........*/"


def test_nested_docstring_normalized(nested_tree, normalization_rule, mutation_context):
    """Verify nested string_content is replaced but delimiters are untouched."""
    records = normalization_rule.apply(nested_tree, mutation_context)

    content_node = nested_tree.children[0].children[1]
    assert content_node.text == "........"
    assert records[0].metadata["new_val"] == "........"


def test_mutation_records_structure(flat_tree, normalization_rule, mutation_context):
    """Verify records have correct action and metadata."""
    records = normalization_rule.apply(flat_tree, mutation_context)

    # Define what we expect to see across all records
    expected_values = {"//........", "/*........*/"}
    # Collect all actual values generated
    actual_values = {rec.metadata["new_val"] for rec in records}

    # Assert that the sets are identical
    assert actual_values == expected_values
    assert len(records) == 2
    # Verify the action for all records
    for rec in records:
        assert rec.action == MutationAction.REFORMAT


# ===== Edge Cases =====


def test_no_comments_tree(normalization_rule, mutation_context):
    """Verify tree with no comments remains unchanged."""
    root = Node((0, 0), (0, 0), "program", children=[Node((1, 0), (1, 1), "identifier", text="x")])

    records = normalization_rule.apply(root, mutation_context)

    assert records == []
    assert root.children[0].text == "x"


def test_empty_tree(normalization_rule, mutation_context):
    """Verify empty tree returns no records."""
    root = Node((0, 0), (0, 0), "program")

    records = normalization_rule.apply(root, mutation_context)

    assert records == []

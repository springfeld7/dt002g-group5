"""Unit tests for whitespace_normalization.py

Validates that the WhitespaceNormalizationRule correctly normalizes whitespace
in a CST, including indentation snapping, tab expansion, inline collapsing,
trailing whitespace removal, padding removal around brackets, and insertion
of structural spaces around commas and operators.
"""

import pytest
from src.transtructiver.mutation.rules.whitespace_normalization import WhitespaceNormalizationRule
from src.transtructiver.mutation.rules.mutation_rule import MutationRecord
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.node import Node


# ===== Helpers =====


def make_indentation_tree():
    """Tree containing indentation whitespace."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 1), "whitespace", text="\t"),
            Node((0, 1), (0, 2), "identifier", text="x"),
        ],
    )


def make_inline_whitespace_tree():
    """Tree containing excessive inline whitespace."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 1), "identifier", text="x"),
            Node((0, 1), (0, 4), "whitespace", text="   "),
            Node((0, 4), (0, 5), "identifier", text="y"),
        ],
    )


def make_bracket_padding_tree():
    """Tree containing whitespace padding inside parentheses and square brackets."""
    children = [
        Node((0, 0), (0, 1), "(", text="("),
        Node((0, 1), (0, 2), "whitespace", text=" "),
        Node((0, 2), (0, 3), "number", text="5"),
        Node((0, 3), (0, 4), "whitespace", text=" "),
        Node((0, 4), (0, 5), ")", text=")"),
        Node((0, 5), (0, 6), "[", text="["),
        Node((0, 6), (0, 7), "whitespace", text=" "),
        Node((0, 7), (0, 8), "number", text="1"),
        Node((0, 8), (0, 9), "whitespace", text=" "),
        Node((0, 9), (0, 10), "]", text="]"),
    ]

    root = Node((0, 0), (0, 0), "program", text="", children=children)

    for c in children:
        c.parent = root

    return root


def make_operator_spacing_tree():
    """Tree with missing spacing around an operator."""
    plus = Node((0, 1), (0, 2), "+", text="+")
    plus.field = "operator"

    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 1), "(", text="("),
            Node((0, 1), (0, 2), "number", text="5"),
            plus,
            Node((0, 2), (0, 3), "number", text="5"),
            Node((0, 3), (0, 4), ")", text=")"),
        ],
    )


def make_comma_spacing_tree():
    """Tree missing a space after a comma."""
    return Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 1), "identifier", text="a"),
            Node((0, 1), (0, 2), ",", text=","),
            Node((0, 2), (0, 3), "identifier", text="b"),
        ],
    )


def make_negative_number_tree():
    """Tree representing a negative number literal: -10"""
    minus = Node((0, 0), (0, 1), "-", text="-")
    number = Node(
        (0, 1), (0, 3), "integer", text="10"
    )  # could be float, decimal_floating_point, etc.
    minus.parent = None
    number.parent = None

    root = Node((0, 0), (0, 0), "program", children=[minus, number])

    # set parents
    minus.parent = root
    number.parent = root

    return root, minus, number


def collect_texts(root: Node):
    """Collect all node texts from a tree."""
    return [n.text for n in root.traverse() if hasattr(n, "text")]


# ===== Fixtures =====


@pytest.fixture
def whitespace_rule():
    """Reusable WhitespaceNormalizationRule instance."""
    return WhitespaceNormalizationRule()


# ===== Positive Cases =====


def test_tab_indentation_expands_and_snaps(whitespace_rule):
    """Tabs at indentation should expand to base_unit spaces."""
    tree = make_indentation_tree()

    whitespace_rule.apply(tree)
    texts = collect_texts(tree)

    assert " " * whitespace_rule.base_unit in texts


def test_inline_whitespace_collapses(whitespace_rule):
    """Multiple inline spaces should collapse to a single space."""
    tree = make_inline_whitespace_tree()

    whitespace_rule.apply(tree)

    texts = collect_texts(tree)

    assert "   " not in texts
    assert " " in texts


def test_padding_inside_parentheses_removed(whitespace_rule):
    """Whitespace inside parentheses should be removed."""
    tree = make_bracket_padding_tree()

    whitespace_rule.apply(tree)

    texts = collect_texts(tree)

    # no space next to parentheses

    assert "( " not in "".join(texts)
    assert " )" not in "".join(texts)


def test_padding_inside_square_brackets_removed(whitespace_rule):
    """Whitespace inside square brackets should be removed."""
    tree = make_bracket_padding_tree()

    whitespace_rule.apply(tree)

    texts = collect_texts(tree)

    assert "[ " not in "".join(texts)
    assert " ]" not in "".join(texts)


def test_operator_spacing_inserted(whitespace_rule):
    """Missing whitespace around operators should be inserted."""
    tree = make_operator_spacing_tree()

    whitespace_rule.apply(tree)

    texts = collect_texts(tree)

    assert "5" in texts
    assert "+" in texts
    assert " " in texts


def test_comma_spacing_inserted(whitespace_rule):
    """Missing whitespace after commas should be inserted."""
    tree = make_comma_spacing_tree()

    whitespace_rule.apply(tree)

    children = tree.children

    for i, node in enumerate(children[:-1]):
        if node.type == ",":
            assert children[i + 1].type == "whitespace"
            assert children[i + 1].text == " "


def test_idempotency_of_comma_spacing(whitespace_rule):
    """Running the rule twice should result in zero additional mutations."""
    tree = make_comma_spacing_tree()

    # First pass: should perform insertion
    records1 = whitespace_rule.apply(tree)
    assert len(records1) > 0
    assert any(r.action == MutationAction.INSERT for r in records1)

    # Second pass: should find everything already normalized
    records2 = whitespace_rule.apply(tree)
    assert len(records2) == 0


def test_inserted_node_properties(whitespace_rule):
    """Verify that inserted whitespace nodes have valid parent pointers and sentinel coordinates."""
    tree = make_comma_spacing_tree()

    whitespace_rule.apply(tree)

    # The comma is at index 1, so the new whitespace should be at index 2
    inserted_node = tree.children[2]

    assert inserted_node.type == "whitespace"
    assert inserted_node.text == " "
    assert inserted_node.start_point == (-1, -1)
    assert inserted_node.parent == tree


def test_mutation_records_generated(whitespace_rule):
    """Whitespace normalization should generate MutationRecords."""
    tree = make_inline_whitespace_tree()

    records = whitespace_rule.apply(tree)

    assert len(records) > 0
    for rec in records:
        assert isinstance(rec, MutationRecord)
        assert rec.action in (MutationAction.REFORMAT, MutationAction.INSERT)


def test_synthetic_whitespace_unique_negative_coordinates(whitespace_rule):
    """Ensure synthetic whitespace nodes have unique negative start_point rows."""
    tree = make_comma_spacing_tree()  # a tree missing space after a comma

    records = whitespace_rule.apply(tree)

    # Collect all synthetic nodes inserted
    synthetic_nodes = [
        child for child in tree.children if child.type == "whitespace" and child.start_point[0] < 0
    ]

    assert len(synthetic_nodes) > 0, "No synthetic whitespace nodes were inserted."

    # All start_point row values should be unique
    start_rows = [n.start_point[0] for n in synthetic_nodes]
    assert len(start_rows) == len(
        set(start_rows)
    ), "Synthetic whitespace nodes have duplicate negative row coordinates."

    # They should all be negative
    assert all(
        r < 0 for r in start_rows
    ), "All synthetic whitespace nodes must have negative row coordinates."


# ===== Edge Cases =====


def test_tree_without_whitespace(whitespace_rule):
    """Tree without whitespace should produce no mutations."""
    tree = Node((0, 0), (0, 0), "program", children=[Node((0, 0), (0, 1), "identifier", text="x")])

    records = whitespace_rule.apply(tree)

    assert records == []


def test_empty_tree_returns_no_records(whitespace_rule):
    """Applying rule to an empty tree should produce no records."""
    root = Node((0, 0), (0, 0), "program")

    records = whitespace_rule.apply(root)

    assert records == []
    assert root.children == []


def test_mixed_reformat_and_insert(whitespace_rule):
    """Verify that a single pass handles both REFORMAT (for tabs) and INSERT (for commas)."""
    # Create a tree with a tab at the start and a missing space after a comma
    tree = Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node((0, 0), (0, 1), "whitespace", text="\t"),
            Node((0, 1), (0, 2), "identifier", text="x"),
            Node((0, 2), (0, 3), ",", text=","),
            Node((0, 3), (0, 4), "identifier", text="y"),
        ],
    )

    # Link parents
    for child in tree.children:
        child.parent = tree

    records = whitespace_rule.apply(tree)

    actions = [r.action for r in records]
    assert MutationAction.REFORMAT in actions
    assert MutationAction.INSERT in actions
    assert len(tree.children) == 5  # Ensure the node was actually added


def test_handle_missing_field_gracefully(whitespace_rule):
    """Ensure rule handles nodes without 'field' attributes without crashing."""
    tree = Node(
        (0, 0), (0, 0), "program", children=[Node((0, 0), (0, 1), "type_with_no_field", text="x")]
    )
    # Should not raise AttributeError
    try:
        whitespace_rule.apply(tree)
    except AttributeError as e:
        pytest.fail(f"Whitespace rule crashed on node without 'field': {e}")


def test_rounding_behavior(whitespace_rule):
    """Ensure 2 spaces with base_unit=4 rounds to 4 (snapping up)."""
    # 2 is exactly halfway, distance_up (2) <= distance_down (2) should snap up
    whitespace_rule.base_unit = 4
    tree = Node((0, 0), (0, 0), "program", children=[Node((0, 0), (0, 1), "whitespace", text="  ")])
    tree.children[0].parent = tree

    whitespace_rule.apply(tree)
    assert tree.children[0].text == "    "


def test_no_space_between_minus_and_number(whitespace_rule):
    """Negative numeric literals should not have a space inserted after the minus."""
    root, minus, number = make_negative_number_tree()

    records = whitespace_rule.apply(root)

    # The minus and number nodes should remain consecutive
    children = root.children
    assert children[0] is minus
    assert children[1] is number

    # No INSERT mutation should target this minus node
    assert all(
        not (r.action == MutationAction.INSERT and r.insertion_point == minus.end_point)
        for r in records
    )


def test_snap_to_grid_logic(whitespace_rule):
    """Verify that _snap_to_grid correctly rounds up, down, and handles exact multiples."""
    base = 4

    # Already a multiple (remainder 0)
    assert whitespace_rule._snap_to_grid(8, base) == 8

    # Round down: remainder 1 (distance_down 1 < distance_up 3)
    assert whitespace_rule._snap_to_grid(5, base) == 4

    # Round up: remainder 3 (distance_up 1 < distance_down 3)
    assert whitespace_rule._snap_to_grid(7, base) == 8

    # Halfway case: remainder 2 (distance_up 2 == distance_down 2)
    # Your logic snaps UP: indent + distance_up (6 + 2 = 8)
    assert whitespace_rule._snap_to_grid(6, base) == 8


def test_nested_structural_spacing(whitespace_rule):
    """Ensure rule normalizes spacing deep within a nested tree."""
    # Build: [program [if [condition , expression]]]
    tree = Node(
        (0, 0),
        (0, 0),
        "program",
        children=[
            Node(
                (0, 0),
                (0, 0),
                "if",
                children=[
                    Node(
                        (0, 0),
                        (0, 0),
                        "condition",
                        children=[
                            Node((0, 0), (0, 0), "a"),
                            Node((0, 0), (0, 0), ","),
                            Node((0, 0), (0, 0), "b"),
                        ],
                    )
                ],
            )
        ],
    )
    # Link parents (crucial for _is_trailing_whitespace and others)
    tree.children[0].parent = tree
    tree.children[0].children[0].parent = tree.children[0]
    for c in tree.children[0].children[0].children:
        c.parent = tree.children[0].children[0]

    whitespace_rule.apply(tree)
    # Check if a space was inserted in the deeply nested list
    assert tree.children[0].children[0].children[1].type == ","
    assert tree.children[0].children[0].children[2].type == "whitespace"

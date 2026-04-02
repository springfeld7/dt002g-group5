"""Unit tests for CStyleIndent strategy.

Verifies:
- Correct prefix selection from first whitespace child.
- Fallback behavior when no whitespace child exists.
- Deterministic behavior for repeated calls.
- Handling of edge cases (empty children, missing attributes).
"""

import pytest
from src.transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.cstyle_strategy import (
    CStyleInsertionStrategy,
)


# ===== Setup =====


class DummyChild:
    """Minimal representation of a node child with type and text."""

    def __init__(self, type_: str, text: str):
        self.type = type_
        self.text = text


class DummyNode:
    """Minimal node representation with children."""

    def __init__(self, children):
        self.children = children


@pytest.fixture
def strategy():
    """Provides a CStyleInsertionStrategy instance."""
    return CStyleInsertionStrategy()


# ===== Indentation Logic =====


def test_prefix_from_whitespace_child(strategy):
    """Prefix should match text of first whitespace child node."""
    children = [
        DummyChild("code", "x=1;"),
        DummyChild("whitespace", "    "),
        DummyChild("newline", "\n"),
        DummyChild("code", "y=2;"),
    ]
    node = DummyNode(children=children)
    assert strategy.get_indent_prefix(node) == "    "


def test_first_whitespace_selected(strategy):
    """Only the first whitespace child should be used."""
    children = [
        DummyChild("whitespace", "  "),
        DummyChild("newline", "\n"),
        DummyChild("whitespace", "    "),
    ]
    node = DummyNode(children=children)
    assert strategy.get_indent_prefix(node) == "  "  # first one only


def test_no_whitespace_returns_none(strategy):
    """If no whitespace child exists, returns None."""
    children = [DummyChild("code", "x=1;"), DummyChild("code", "y=2;")]
    node = DummyNode(children=children)
    assert strategy.get_indent_prefix(node) is None


def test_empty_children_returns_none(strategy):
    """Node with no children returns None."""
    node = DummyNode(children=[])
    assert strategy.get_indent_prefix(node) is None


def test_missing_children_attribute_raises(strategy):
    """Node without children attribute raises AttributeError."""

    class BareNode:
        pass

    node = BareNode()
    with pytest.raises(AttributeError):
        strategy.get_indent_prefix(node)


def test_multiple_mixed_children(strategy):
    """Handles mixed children with whitespace interleaved."""
    children = [
        DummyChild("code", "int x;"),
        DummyChild("whitespace", "\t"),
        DummyChild("newline", "\n"),
        DummyChild("code", "y=0;"),
        DummyChild("whitespace", "    "),
    ]
    node = DummyNode(children=children)
    # Only the first whitespace should be selected
    assert strategy.get_indent_prefix(node) == "\t"


def test_prefix_with_whitespace_no_newline(strategy):
    """If no newline child exists, get_indent_prefix should return None even if whitespace exists."""
    children = [
        DummyChild("code", "x=1;"),
        DummyChild("whitespace", "    "),
        DummyChild("code", "y=2;"),
    ]
    node = DummyNode(children=children)
    assert strategy.get_indent_prefix(node) is None


# ===== Gap Validation Logic =====


def test_valid_gap_after_newline(strategy):
    """Gap is valid when preceding node is a newline."""
    preceding = DummyChild("newline", "\n")
    current = DummyChild("code", "x=1;")

    assert strategy.is_valid_gap(current, preceding) is True


def test_invalid_gap_without_newline(strategy):
    """Gap is invalid if not preceded by a newline."""
    preceding = DummyChild("code", "x=1;")
    current = DummyChild("code", "y=2;")

    assert strategy.is_valid_gap(current, preceding) is False


def test_invalid_gap_before_opening_brace(strategy):
    """Should never allow insertion before an opening brace."""
    preceding = DummyChild("newline", "\n")
    current = DummyChild("{", "{")

    assert strategy.is_valid_gap(current, preceding) is False


def test_valid_gap_ignores_current_type_if_not_brace(strategy):
    """Current node type should not affect validity unless it is '{'."""
    preceding = DummyChild("newline", "\n")
    current = DummyChild("}", "}")

    assert strategy.is_valid_gap(current, preceding) is True


# ===== Terminal Detection =====


def test_terminal_return_statement(strategy):
    """Return statements should be identified as terminal."""
    node = DummyChild("return_statement", "return x;")
    assert strategy.is_terminal(node) is True


def test_terminal_break_statement(strategy):
    """Break statements should be identified as terminal."""
    node = DummyChild("break_statement", "break;")
    assert strategy.is_terminal(node) is True


def test_terminal_continue_statement(strategy):
    """Continue statements should be identified as terminal."""
    node = DummyChild("continue_statement", "continue;")
    assert strategy.is_terminal(node) is True


def test_non_terminal_statement(strategy):
    """Non-terminal statements should return False."""
    node = DummyChild("expression_statement", "x = 1;")
    assert strategy.is_terminal(node) is False


def test_terminal_with_unexpected_type(strategy):
    """Unknown node types should not be considered terminal."""
    node = DummyChild("throw_statement", "throw e;")
    assert strategy.is_terminal(node) is False

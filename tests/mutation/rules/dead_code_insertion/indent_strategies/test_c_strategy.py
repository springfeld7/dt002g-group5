"""Unit tests for CStyleIndent strategy.

Verifies:
- Correct prefix selection from first whitespace child.
- Fallback behavior when no whitespace child exists.
- Deterministic behavior for repeated calls.
- Handling of edge cases (empty children, missing attributes).
"""

import pytest
from src.transtructiver.mutation.rules.dead_code_insertion.indent_strategies.c_strategy import (
    CStyleIndent,
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
    """Provides a CStyleIndent instance."""
    return CStyleIndent()


# ===== Indentation Logic =====


def test_prefix_from_whitespace_child(strategy):
    """Prefix should match text of first whitespace child node."""
    children = [
        DummyChild("code", "x=1;"),
        DummyChild("whitespace", "    "),
        DummyChild("code", "y=2;"),
    ]
    node = DummyNode(children=children)
    assert strategy.get_prefix(node) == "    "


def test_first_whitespace_selected(strategy):
    """Only the first whitespace child should be used."""
    children = [
        DummyChild("whitespace", "  "),
        DummyChild("whitespace", "    "),
    ]
    node = DummyNode(children=children)
    assert strategy.get_prefix(node) == "  "  # first one only


def test_no_whitespace_returns_none(strategy):
    """If no whitespace child exists, returns None."""
    children = [DummyChild("code", "x=1;"), DummyChild("code", "y=2;")]
    node = DummyNode(children=children)
    assert strategy.get_prefix(node) is None


def test_empty_children_returns_none(strategy):
    """Node with no children returns None."""
    node = DummyNode(children=[])
    assert strategy.get_prefix(node) is None


def test_deterministic_behavior(strategy):
    """Repeated calls with the same node produce identical prefix."""
    children = [DummyChild("whitespace", "    ")]
    node = DummyNode(children=children)
    prefix1 = strategy.get_prefix(node)
    prefix2 = strategy.get_prefix(node)
    assert prefix1 == prefix2


def test_non_string_text_works(strategy):
    """Whitespace node with non-string text is returned as-is."""
    children = [DummyChild("whitespace", 5)]  # numeric text
    node = DummyNode(children=children)
    # Should return the value as-is
    assert strategy.get_prefix(node) == 5


def test_missing_children_attribute_raises(strategy):
    """Node without children attribute raises AttributeError."""

    class BareNode:
        pass

    node = BareNode()
    with pytest.raises(AttributeError):
        strategy.get_prefix(node)


def test_multiple_mixed_children(strategy):
    """Handles mixed children with whitespace interleaved."""
    children = [
        DummyChild("code", "int x;"),
        DummyChild("whitespace", "\t"),
        DummyChild("code", "y=0;"),
        DummyChild("whitespace", "    "),
    ]
    node = DummyNode(children=children)
    # Only the first whitespace should be selected
    assert strategy.get_prefix(node) == "\t"

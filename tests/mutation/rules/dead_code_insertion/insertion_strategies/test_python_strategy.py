"""Unit tests for PythonInsertionStrategy.

Verifies:
- Correct calculation of indentation from node.start_point[1].
- Handling of edge cases (zero indentation, large indentation, missing attributes).
- Deterministic behavior for repeated calls.
- Correct validation of insertion gaps.
- Proper identification of terminal statements.
"""

import pytest
from src.transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.python_strategy import (
    PythonInsertionStrategy,
)

# ===== Setup =====


class DummyNode:
    """Minimal flexible node supporting both indentation and structural checks."""

    def __init__(self, type_: str | None = None, text: str = "", column: int | None = None):
        """
        Args:
            type_ (str | None): Node type (used in gap + terminal logic).
            text (str): Node text (not strictly required, but included for consistency).
            column (int | None): Column index for indentation (maps to start_point[1]).
        """
        self.type = type_
        self.text = text

        if column is not None:
            self.start_point = (0, column)


@pytest.fixture
def strategy():
    """Provides a PythonInsertionStrategy instance."""
    return PythonInsertionStrategy()


# ===== Indentation Logic =====


def test_zero_indent(strategy):
    """Prefix should be empty string when column is 0."""
    node = DummyNode(column=0)
    assert strategy.get_indent_prefix(node) == ""


def test_standard_indent(strategy):
    """Prefix matches column number in spaces."""
    node = DummyNode(column=4)
    assert strategy.get_indent_prefix(node) == "    "


def test_large_indent(strategy):
    """Prefix scales correctly for large column values."""
    node = DummyNode(column=20)
    prefix = strategy.get_indent_prefix(node)
    assert len(prefix) == 20
    assert set(prefix) == {" "}


def test_deterministic_behavior(strategy):
    """Repeated calls with the same node produce identical results."""
    node = DummyNode(column=8)
    prefix1 = strategy.get_indent_prefix(node)
    prefix2 = strategy.get_indent_prefix(node)
    assert prefix1 == prefix2


def test_non_integer_column_raises(strategy):
    """Non-integer column should raise TypeError when multiplied."""

    class BadNode:
        start_point = (0, "4")  # invalid type

    node = BadNode()
    with pytest.raises(TypeError):
        strategy.get_indent_prefix(node)


def test_missing_start_point_attribute(strategy):
    """Node without start_point attribute should raise AttributeError."""

    class BareNode:
        pass

    node = BareNode()
    with pytest.raises(AttributeError):
        strategy.get_indent_prefix(node)


def test_custom_node(strategy):
    """Supports any node with start_point[1] integer."""

    class CustomNode:
        def __init__(self, column):
            self.start_point = (5, column)

    node = CustomNode(column=7)
    assert strategy.get_indent_prefix(node) == "       "  # 7 spaces


# ===== Gap Validation Logic =====


def test_valid_gap_at_block_start(strategy):
    """Gap is valid at the start of a block (preceding is None)."""
    current = DummyNode(type_="code")
    preceding = None

    assert strategy.is_valid_gap(current, preceding) is True


def test_valid_gap_after_newline(strategy):
    """Gap is valid when preceded by a newline."""
    preceding = DummyNode(type_="newline")
    current = DummyNode(type_="code")

    assert strategy.is_valid_gap(current, preceding) is True


def test_invalid_gap_without_newline(strategy):
    """Gap is invalid if preceding node is not a newline."""
    preceding = DummyNode(type_="code")
    current = DummyNode(type_="code")

    assert strategy.is_valid_gap(current, preceding) is False


def test_valid_gap_ignores_current_type(strategy):
    """Current node type does not affect gap validity."""
    preceding = DummyNode(type_="newline")
    current = DummyNode(type_="pass_statement")

    assert strategy.is_valid_gap(current, preceding) is True


# ===== Terminal Detection =====


def test_terminal_return_statement(strategy):
    """Return statements should be identified as terminal."""
    node = DummyNode(type_="return_statement")
    assert strategy.is_terminal(node) is True


def test_terminal_break_statement(strategy):
    """Break statements should be identified as terminal."""
    node = DummyNode(type_="break_statement")
    assert strategy.is_terminal(node) is True


def test_terminal_continue_statement(strategy):
    """Continue statements should be identified as terminal."""
    node = DummyNode(type_="continue_statement")
    assert strategy.is_terminal(node) is True


def test_terminal_pass_statement(strategy):
    """Pass statements should be identified as terminal."""
    node = DummyNode(type_="pass_statement")
    assert strategy.is_terminal(node) is True


def test_non_terminal_statement(strategy):
    """Non-terminal statements should return False."""
    node = DummyNode(type_="expression_statement")
    assert strategy.is_terminal(node) is False


def test_non_terminal_raise_statement(strategy):
    """Raise is not considered terminal in this implementation."""
    node = DummyNode(type_="raise_statement")
    assert strategy.is_terminal(node) is False

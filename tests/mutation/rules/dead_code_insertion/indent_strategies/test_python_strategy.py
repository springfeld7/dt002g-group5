"""Unit tests for PythonIndent strategy.

Verifies:
- Correct calculation of indentation from node.start_point[1].
- Handling of edge cases (zero indentation, large indentation, missing attributes).
- Deterministic behavior for repeated calls.
"""

import pytest
from src.transtructiver.mutation.rules.dead_code_insertion.indent_strategies.python_strategy import (
    PythonIndent,
)

# ===== Setup =====


class DummyNode:
    """Minimal node representation with start_point (line, column)."""

    def __init__(self, column: int):
        self.start_point = (0, column)


@pytest.fixture
def strategy():
    """Provides a PythonIndent instance."""
    return PythonIndent()


# ===== Indentation Logic =====


def test_zero_indent(strategy):
    """Prefix should be empty string when column is 0."""
    node = DummyNode(column=0)
    assert strategy.get_prefix(node) == ""


def test_standard_indent(strategy):
    """Prefix matches column number in spaces."""
    node = DummyNode(column=4)
    assert strategy.get_prefix(node) == "    "


def test_large_indent(strategy):
    """Prefix scales correctly for large column values."""
    node = DummyNode(column=20)
    prefix = strategy.get_prefix(node)
    assert len(prefix) == 20
    assert set(prefix) == {" "}


def test_deterministic_behavior(strategy):
    """Repeated calls with the same node produce identical results."""
    node = DummyNode(column=8)
    prefix1 = strategy.get_prefix(node)
    prefix2 = strategy.get_prefix(node)
    assert prefix1 == prefix2


def test_non_integer_column_raises(strategy):
    """Non-integer column should raise TypeError when multiplied."""

    class BadNode:
        start_point = (0, "4")  # string instead of int

    node = BadNode()
    with pytest.raises(TypeError):
        strategy.get_prefix(node)


def test_missing_start_point_attribute(strategy):
    """Node without start_point attribute should raise AttributeError."""

    class BareNode:
        pass

    node = BareNode()
    with pytest.raises(AttributeError):
        strategy.get_prefix(node)


def test_custom_node(strategy):
    """Supports any node with start_point[1] integer."""

    class CustomNode:
        def __init__(self, column):
            self.start_point = (5, column)

    node = CustomNode(column=7)
    assert strategy.get_prefix(node) == "       "  # 7 spaces

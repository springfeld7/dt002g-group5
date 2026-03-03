"""Unit tests for the MutationRule abstract base class and LocalChangeRecord schema.

This module verifies:
- The abstract nature of the MutationRule class (cannot be instantiated).
- Correct initialization of rule metadata (e.g., automatic name assignment).
- Compliance of concrete implementations with the LocalChangeRecord schema.
- Support for both original source nodes and synthetic/inserted nodes.

Testing is performed using minimal concrete subclasses to validate the 
interface contract before integration into the MutationEngine.
"""

import pytest
from typing import List
from src.transtructiver.mutation.mutation_rule import MutationRule, LocalChangeRecord


def test_cannot_instantiate_abc():
    """Ensure that the MutationRule ABC cannot be instantiated directly."""
    with pytest.raises(TypeError):
        MutationRule()


def test_concrete_rule_implementation():
    """Test a minimal valid implementation of a MutationRule."""

    class RenameVariableRule(MutationRule):
        def apply(self, root) -> List[LocalChangeRecord]:
            return [{"node_id": (10, 5), "action": "RENAME", "metadata": {"new_text": "x_var"}}]

    rule = RenameVariableRule()

    # Verify automatic name assignment in __init__
    assert rule.name == "RenameVariableRule"

    # Verify return structure
    results = rule.apply(None)
    assert isinstance(results, list)
    assert results[0]["node_id"] == (10, 5)
    assert results[0]["action"] == "RENAME"


def test_synthetic_node_record():
    """Verify that node_id can be None for synthetic/inserted nodes."""

    class InsertDeadCodeRule(MutationRule):
        def apply(self, root) -> List[LocalChangeRecord]:
            return [
                {
                    "node_id": None,
                    "action": "INSERT",
                    "metadata": {"path": "0.1", "type": "opaque_predicate"},
                }
            ]

    rule = InsertDeadCodeRule()
    results = rule.apply(None)

    assert results[0]["node_id"] is None
    assert results[0]["action"] == "INSERT"


def test_repr_output():
    """Verify the string representation for debugging."""

    class TestRule(MutationRule):
        def apply(self, root):
            return []

    rule = TestRule()
    assert repr(rule) == "<TestRule>"

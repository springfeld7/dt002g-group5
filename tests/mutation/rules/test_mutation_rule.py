"""Unit tests for the MutationRule abstract base class and MutationRecord schema.

This module verifies:
- The abstract nature of the MutationRule class (cannot be instantiated).
- Correct initialization of rule metadata (e.g., automatic name assignment).
- Compliance of concrete implementations with the MutationRecord schema.
- Proper use of the MutationAction enum for type-safe reporting.
- Support for both original source nodes and synthetic/inserted nodes.

Testing is performed using minimal concrete subclasses to validate the 
interface contract before integration into the MutationEngine.
"""

import pytest
from typing import List
from src.transtructiver.mutation.rules.mutation_rule import MutationRule, MutationRecord
from src.transtructiver.mutation.mutation_types import MutationAction


def test_cannot_instantiate_abc():
    """Ensure that the MutationRule ABC cannot be instantiated directly."""
    with pytest.raises(TypeError):
        MutationRule()  # type: ignore[abstract]


def test_concrete_rule_implementation():
    """Test a minimal valid implementation of a MutationRule."""

    class RenameVariableRule(MutationRule):
        def apply(self, root) -> List[MutationRecord]:
            # Now returning an actual object, not a dict
            return [
                MutationRecord(
                    node_id=(10, 5),
                    action=MutationAction.RENAME,
                    metadata={"new_val": "x_var"},  # Fixed key from 'new_text' to 'new_val'
                )
            ]

    rule = RenameVariableRule()

    rule = RenameVariableRule()
    assert rule.name == "RenameVariableRule"

    results = rule.apply(None)  # type: ignore[abstract]
    assert isinstance(results[0], MutationRecord)
    assert results[0].node_id == (10, 5)
    assert results[0].action == MutationAction.RENAME


def test_synthetic_node_record():
    """Verify synthetic nodes can use negative coordinates"""

    class InsertDeadCodeRule(MutationRule):
        def apply(self, root) -> List[MutationRecord]:
            return [
                MutationRecord(
                    node_id=(-1, -1),
                    action=MutationAction.INSERT,
                    metadata={
                        "new_val": "pass",
                        "node_type": "stmt",
                        "insertion_point": (0, 0),  # required by verifier
                    },
                )
            ]

    rule = InsertDeadCodeRule()
    results = rule.apply(None)  # type: ignore[abstract]

    # Check synthetic coordinates
    assert results[0].node_id[0] < 0
    # Check action
    assert results[0].action == MutationAction.INSERT
    # Check insertion_point exists
    assert "insertion_point" in results[0].metadata
    assert results[0].metadata["insertion_point"] == (0, 0)


def test_invalid_metadata_raises_error():
    """Verify that malformed records blow up immediately (the new behavior)."""
    with pytest.raises(ValueError, match="missing required key"):
        MutationRecord(
            node_id=(1, 1), action=MutationAction.RENAME, metadata={}  # Missing 'new_val'
        )


def test_repr_output():
    """Verify the string representation for debugging."""

    class TestRule(MutationRule):
        def apply(self, root):
            return []

    rule = TestRule()
    assert repr(rule) == "<TestRule>"

"""Unit tests for verification_strategy.py

Validates the abstract VerificationStrategy class contract.
Ensures that concrete subclasses implement verify() correctly and return a list of errors.
"""

import pytest
from abc import ABC, abstractmethod
from typing import List, Optional

from src.transtructiver.verification.strategies.verification_strategy import VerificationStrategy
from src.transtructiver.mutation.mutation_manifest import ManifestEntry
from src.transtructiver.node import Node


# ===== Helper Concrete Strategy =====


class DummyStrategy(VerificationStrategy):
    """Minimal concrete strategy for testing."""

    def verify(self, orig: Optional[Node], mut: Optional[Node], entry: ManifestEntry) -> List[str]:
        return ["dummy error"]


# ===== Tests =====


def test_cannot_instantiate_abc():
    """Direct instantiation of VerificationStrategy should raise TypeError."""
    with pytest.raises(TypeError):
        VerificationStrategy()


def test_dummy_strategy_returns_list():
    """A concrete subclass must return a list of strings from verify()."""
    dummy = DummyStrategy()

    # Create a fake ManifestEntry for testing
    entry = ManifestEntry(original_id=(0, 0), history=[], metadata={})

    result = dummy.verify(None, None, entry)

    assert isinstance(result, list)
    assert all(isinstance(e, str) for e in result)
    assert result == ["dummy error"]


def test_dummy_strategy_accepts_optional_nodes():
    """Verify method should accept None for orig or mut."""
    dummy = DummyStrategy()
    entry = ManifestEntry(original_id=(0, 0), history=[], metadata={})

    # Both nodes None
    result1 = dummy.verify(None, None, entry)
    # Only orig
    result2 = dummy.verify(
        Node(type="A", text="a", start_point=(0, 0), end_point=(0, 1), children=[]), None, entry
    )
    # Only mut
    result3 = dummy.verify(
        None, Node(type="B", text="b", start_point=(1, 0), end_point=(1, 1), children=[]), entry
    )

    assert all(isinstance(r, list) for r in [result1, result2, result3])

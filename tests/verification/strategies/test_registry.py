"""Unit tests for strategies/registry.py

Validates that STRATEGY_MAP correctly associates each MutationAction
with the appropriate VerificationStrategy subclass.
"""

import pytest
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.verification.strategies.registry import STRATEGY_MAP
from src.transtructiver.verification.strategies.content_strategy import ContentVerificationStrategy
from src.transtructiver.verification.strategies.delete_strategy import DeleteVerificationStrategy
from src.transtructiver.verification.strategies.insert_strategy import InsertVerificationStrategy
from src.transtructiver.verification.strategies.substitute_strategy import (
    SubstituteVerificationStrategy,
)
from src.transtructiver.verification.strategies.flatten_strategy import FlattenVerificationStrategy


@pytest.mark.parametrize(
    "action,expected_class",
    [
        (MutationAction.RENAME, ContentVerificationStrategy),
        (MutationAction.REFORMAT, ContentVerificationStrategy),
        (MutationAction.DELETE, DeleteVerificationStrategy),
        (MutationAction.INSERT, InsertVerificationStrategy),
        (MutationAction.SUBSTITUTE, SubstituteVerificationStrategy),
        (MutationAction.FLATTEN, FlattenVerificationStrategy),
    ],
)
def test_strategy_map(action, expected_class):
    """
    Test that each MutationAction maps to the correct strategy class.
    """
    strategy = STRATEGY_MAP.get(action)
    assert strategy is not None, f"No strategy registered for {action}"
    assert isinstance(
        strategy, expected_class
    ), f"{action} maps to {type(strategy)}, expected {expected_class}"

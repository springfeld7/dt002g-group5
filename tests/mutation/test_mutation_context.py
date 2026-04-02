"""Unit tests for the MutationContext class."""

import pytest
from src.transtructiver.mutation.mutation_context import MutationContext


@pytest.fixture
def ctx():
    """Provides a fresh MutationContext with default counter for each test."""
    return MutationContext()


class TestMutationContext:

    def test_initial_counter_default(self, ctx):
        """Initial synthetic_row_counter defaults to -1."""
        assert ctx.synthetic_row_counter == -1

    def test_next_id_returns_current_and_decrements(self, ctx):
        """next_id returns current counter and decrements it."""
        val = ctx.next_id()
        assert val == -1
        assert ctx.synthetic_row_counter == -2

    def test_next_id_multiple_calls(self, ctx):
        """Multiple calls to next_id decrement counter consistently."""
        values = [ctx.next_id() for _ in range(3)]
        assert values == [-1, -2, -3]
        assert ctx.synthetic_row_counter == -4

    def test_next_id_negative_counter(self):
        """next_id works even if counter starts negative."""
        ctx_neg = MutationContext(synthetic_row_counter=-3)
        values = [ctx_neg.next_id() for _ in range(3)]
        assert values == [-3, -4, -5]
        assert ctx_neg.synthetic_row_counter == -6

    def test_next_id_unique_sequence(self, ctx):
        """Ensures each call to next_id produces a unique value."""
        seen = {ctx.next_id(), ctx.next_id(), ctx.next_id()}
        assert len(seen) == 3

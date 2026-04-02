"""Unit tests for the Insertion Strategy Registry."""

import pytest

from transtructiver.exceptions import UnsupportedLanguageError
from transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.registry import (
    get_strategy,
    _STRATEGY_MAP,
)
from transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.python_strategy import (
    PythonInsertionStrategy,
)
from transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.cstyle_strategy import (
    CStyleInsertionStrategy,
)


class TestInsertionStrategyRegistry:

    def test_get_strategy_returns_correct_types(self):
        """Verify the registry returns the expected strategy instances."""
        assert isinstance(get_strategy("python"), PythonInsertionStrategy)
        assert isinstance(get_strategy("java"), CStyleInsertionStrategy)
        assert isinstance(get_strategy("cpp"), CStyleInsertionStrategy)

    def test_get_strategy_is_case_insensitive(self):
        """Verify lookup handles weird casing."""
        assert isinstance(get_strategy("pYtHoN"), PythonInsertionStrategy)
        assert isinstance(get_strategy("JAVA"), CStyleInsertionStrategy)

    def test_get_strategy_handles_whitespace(self):
        """Verify lookup strips surrounding whitespace."""
        assert isinstance(get_strategy("  cpp  "), CStyleInsertionStrategy)

    def test_registry_contains_all_mapped_languages(self):
        """Ensure the public function aligns with the internal map keys."""
        for lang in _STRATEGY_MAP.keys():
            assert get_strategy(lang) is not None

    def test_get_strategy_raises_for_unknown_language(self):
        """
        Verify unsupported languages raise UnsupportedLanguageError
        instead of returning None.
        """
        with pytest.raises(UnsupportedLanguageError) as excinfo:
            get_strategy("nolanguage")

        # Optional: verify the error message contains the offending language
        assert "nolanguage" in str(excinfo.value)

    def test_get_strategy_raises_for_empty_string(self):
        """Verify empty input triggers the custom error."""
        with pytest.raises(UnsupportedLanguageError):
            get_strategy("")

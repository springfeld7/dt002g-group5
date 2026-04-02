"""Unit tests for lexicon/registry.py

Covers verification of language-to-lexicon mapping, case-insensitivity, 
alias handling (e.g., 'cpp' vs 'c++'), and error handling for unsupported languages.
"""

import pytest
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.registry import (
    get_lexicon,
    LEXICON_MAP,
)
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.python_lexicon import (
    PythonLexicon,
)
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.java_lexicon import JavaLexicon
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.cpp_lexicon import CppLexicon
from transtructiver.exceptions import UnsupportedLanguageError


# ===== Positive Cases =====


def test_get_lexicon_success():
    """Should return the correct class for all registered languages."""
    assert get_lexicon("python") is PythonLexicon
    assert get_lexicon("java") is JavaLexicon
    assert get_lexicon("cpp") is CppLexicon


def test_get_lexicon_case_insensitivity():
    """Should be case-insensitive when retrieving lexicon classes."""
    assert get_lexicon("PYTHON") is PythonLexicon
    assert get_lexicon("Java") is JavaLexicon
    assert get_lexicon("cPP") is CppLexicon


def test_get_lexicon_whitespace_handling():
    """Should handle leading/trailing whitespace in language strings."""
    assert get_lexicon("  python  ") is PythonLexicon


# ===== Negative Cases & Edge Cases =====


def test_registry_map_contains_expected_keys():
    """Ensure the underlying map hasn't been accidentally cleared or corrupted."""
    expected_keys = {"python", "java", "cpp"}
    assert expected_keys.issubset(set(LEXICON_MAP.keys()))


@pytest.mark.parametrize("unsupported", ["nolanguage", " ", ""])
def test_get_lexicon_raises_unsupported_language_error(unsupported: str):
    """
    Test that unsupported, whitespace, or empty strings raise UnsupportedLanguageError.

    Args:
        unsupported (str): The invalid language identifier to test.

    Returns:
        None
    """
    with pytest.raises(UnsupportedLanguageError) as exc_info:
        get_lexicon(unsupported)

    # Verify the error message contains the exact input provided
    assert str(exc_info.value) == f"Unsupported language: {unsupported}"

    # Verify the custom 'language' attribute matches the input
    assert exc_info.value.language == unsupported

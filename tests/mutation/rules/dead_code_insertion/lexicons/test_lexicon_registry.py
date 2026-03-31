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


def test_get_lexicon_unsupported_raises_error():
    """Should raise a KeyError with a helpful message for unknown languages."""
    with pytest.raises(KeyError, match="No DeadCodeLexicon registered for language: nolanguage"):
        get_lexicon("nolanguage")


def test_registry_map_contains_expected_keys():
    """Ensure the underlying map hasn't been accidentally cleared or corrupted."""
    expected_keys = {"python", "java", "cpp"}
    assert expected_keys.issubset(set(LEXICON_MAP.keys()))


def test_get_lexicon_empty_string():
    """Should raise KeyError for empty or whitespace-only strings."""
    with pytest.raises(KeyError):
        get_lexicon("")
    with pytest.raises(KeyError):
        get_lexicon("   ")

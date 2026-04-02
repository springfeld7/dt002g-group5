"""Insertion strategies Registry

This module maps language identifiers to their respective insertion strategies.
"""

from transtructiver.mutation.rules.dead_code_insertion.insertion_strategies.insertion_strategy import (
    InsertionStrategy,
)
from transtructiver.exceptions import UnsupportedLanguageError
from .python_strategy import PythonInsertionStrategy
from .cstyle_strategy import CStyleInsertionStrategy

# Global Registry of Language Strategies
_STRATEGY_MAP = {
    "python": PythonInsertionStrategy(),
    "java": CStyleInsertionStrategy(),
    "cpp": CStyleInsertionStrategy(),
}


def get_strategy(language: str) -> InsertionStrategy | None:
    """
    Retrieves the full structural strategy for a given language.

    Args:
        language (str): The language identifier (e.g., 'python', 'java', 'cpp').

    Returns:
        InsertionStrategy | None: The strategy instance, or None if the
                                  language is unsupported.
    """
    clean_lang = language.lower().strip()
    strategy = _STRATEGY_MAP.get(clean_lang)

    if not strategy:
        raise UnsupportedLanguageError(
            f"No insertion strategy found for language: '{language}'. "
            f"Supported: {list(_STRATEGY_MAP.keys())}"
        )

    return strategy

"""lexicons/registry.py

Centralized mapping of language identifiers to their concrete DeadCodeLexicon 
implementations. This allows the InsertDeadCodeRule to remain language-agnostic.
"""

from typing import Dict, Type

from .dead_code_lexicon import DeadCodeLexicon
from .python_lexicon import PythonLexicon
from .java_lexicon import JavaLexicon
from .cpp_lexicon import CppLexicon
from transtructiver.exceptions import UnsupportedLanguageError

# Mapping normalized language strings to their respective Class types
LEXICON_MAP: Dict[str, Type[DeadCodeLexicon]] = {
    "python": PythonLexicon,
    "java": JavaLexicon,
    "cpp": CppLexicon,
}


def get_lexicon(language: str) -> Type[DeadCodeLexicon]:
    """
    Retrieves the appropriate Lexicon class for a given language.

    Args:
        language (str): The language identifier (e.g., 'python', 'java').

    Returns:
        Type[DeadCodeLexicon]: The concrete lexicon class.

    Raises:
        UnsupportedLanguageError: If the language is not supported.
    """
    lang_key = language.lower().strip()
    lexicon_cls = LEXICON_MAP.get(lang_key)
    if lexicon_cls is None:
        raise UnsupportedLanguageError(language)
    return lexicon_cls

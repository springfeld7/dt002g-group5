"""lexicons/registry.py

Centralized mapping of language identifiers to their concrete DeadCodeLexicon 
implementations. This allows the InsertDeadCodeRule to remain language-agnostic.
"""

from typing import Dict, Type
from .dead_code_lexicon import DeadCodeLexicon
from .python_lexicon import PythonLexicon
from .java_lexicon import JavaLexicon
from .cpp_lexicon import CppLexicon

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
        KeyError: If the language is not supported.
    """
    lang_key = language.lower().strip()
    if lang_key not in LEXICON_MAP:
        raise KeyError(f"No DeadCodeLexicon registered for language: {language}")

    return LEXICON_MAP[lang_key]

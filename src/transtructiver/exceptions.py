"""
Custom exception hierarchy for the Transtructiver project.

This module defines domain-specific exceptions used across the system.
Having a centralized exception hierarchy improves error clarity,
debugging, and allows callers to handle failures at the appropriate level
of abstraction.

All custom exceptions should inherit from `TranstructiverError`.
"""


class TranstructiverError(Exception):
    """
    Base exception for all Transtructiver-specific errors.

    This serves as the common ancestor for all custom exceptions in the
    project, allowing callers to catch all domain-related errors with a
    single exception type if desired.
    """

    pass


class UnsupportedLanguageError(TranstructiverError):
    """
    Raised when a requested language is not supported by the system.

    This typically occurs when no lexicon or implementation exists for the
    given language in mutation rules or other language-dependent components.

    Attributes:
        language (str): The unsupported language identifier.
    """

    def __init__(self, language: str):
        """
        Initialize the exception with the unsupported language.

        Args:
            language (str): The language that is not supported.
        """
        self.language = language
        super().__init__(f"Unsupported language: {language}")

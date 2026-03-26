"""dead_code_lexicon.py

Defines the `DeadCodeLexicon` abstract base class and supporting configuration
for generating syntactically valid, semantically inert (dead) code constructs.

This module provides a language-agnostic framework for constructing randomized
dead code fragments, including assignments, opaque conditional branches, and
unreachable loop structures. It separates universal generation logic (e.g.,
random value synthesis and structural composition) from language-specific
rendering, which is delegated to concrete subclasses.

The primary purpose of this module is to support semantics-preserving program
transformations by injecting non-functional code that does not alter runtime
behavior but may affect code structure, readability, or analysis.

Key Features:
- Deterministic randomization via injected `random.Random` instance.
- Configurable primitive value generation (integers, floats, strings).
- Strategy-based dead code generation (assignment, conditional wrapping, loop wrapping).
- Pluggable language backends via abstract method contracts.
- Indentation-aware formatting for seamless integration into target code.

Constants:
    INT_MIN (int): Lower bound for generated integer values.
    INT_MAX (int): Upper bound for generated integer values.
    FLOAT_MIN (float): Lower bound for generated float values.
    FLOAT_MAX (float): Upper bound for generated float values.
    FLOAT_PRECISION (int): Decimal precision for generated floats.
    STR_LENGTH (int): Length of generated random strings.

Intended Usage:
Concrete subclasses implement language-specific syntax rules (e.g., Python,
Java, C++) while relying on this base class for structural generation logic.
This design enables consistent dead code injection across multiple programming
languages within transformation pipelines.
"""

import random
from abc import ABC, abstractmethod
from tempfile import template
from typing import ClassVar, List, Any, Optional
from unittest import case

# Configuration for DeadCodeLexicon
# These values define the range and characteristics of the random values generated for dead code lexicon
INT_MIN = 0
INT_MAX = 100
FLOAT_MIN = 0.1
FLOAT_MAX = 99.9
FLOAT_PRECISION = 2
STR_LENGTH = 5


class DeadCodeLexicon(ABC):
    """
    Abstract Base Class for language-specific dead code generation.

    This lexicon acts as a language-specific generator for synthetic dead code.
    It produces syntactically valid statements and blocks — including dead assignments
    and unreachable control flow.

    Attributes:
        _rng (random.Random): The seeded random instance used for all selections.
        _indent_unit (str): The horizontal whitespace standard (e.g., '    ' or '  ').
        _current_type (Optional[str]): Tracks the type of the current variable for type-safe modifications.
        OPAQUE_PREDICATES (ClassVar[List[str]]): List of boolean expressions that always evaluate to False.
        UNREACHABLE_LOOP_HEADERS (ClassVar[List[str]]): List of loop headers that never execute their body.
        FAKE_USE_PATTERNS (ClassVar[List[str]]): List of template statements for benign variable use.
        IDENTITY_OPS_STR (ClassVar[List[str]]): List of string identity operations that preserve value.
        IDENTITY_OPS_NUMERIC (ClassVar[List[str]]): List of numeric identity operations that preserve value.
    """

    OPAQUE_PREDICATES: ClassVar[List[str]]
    UNREACHABLE_LOOP_HEADERS: ClassVar[List[str]]
    FAKE_USE_PATTERNS: ClassVar[List[str]]
    IDENTITY_OPS_STR: ClassVar[List[str]]
    IDENTITY_OPS_NUMERIC: ClassVar[List[str]]

    def __init__(self, rng: random.Random):
        """
        Initializes the Lexicon.

        Args:
            rng (random.Random): A seeded random instance from the calling Rule.
        """
        self._rng = rng
        self._current_type: Optional[str] = None
        self._indent_unit = "    "  # Default, updated via set_indent_unit()

    def set_indent_unit(self, indent_unit: str) -> None:
        """
        Sets the indentation unit for the lexicon, allowing it to produce
        whitespace that matches the target file's style.

        Args:
            indent_unit (str): The detected or normalized indentation string.
        """
        self._indent_unit = indent_unit

    # --- Universal Raw Data Generators ---

    def _get_raw_int(self) -> int:
        """
        Generates a random integer within the specified range defined in the config.

        Returns:
            int: A raw integer value.
        """
        return self._rng.randint(INT_MIN, INT_MAX)

    def _get_raw_float(self) -> float:
        """
        Generates a random float within the specified range and precision of the config.

        Returns:
            float: A raw float value.
        """
        return round(self._rng.uniform(FLOAT_MIN, FLOAT_MAX), FLOAT_PRECISION)

    def _get_raw_string(self) -> str:
        """
        Generates a random alphanumeric string with the length defined in the config.

        Returns:
            str: A raw string of characters.
        """
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(self._rng.choices(chars, k=STR_LENGTH))

    # --- Core Generation Logic ---

    def get_random_dead_code(self, var_name: str, loop_var: str, prefix: str) -> str:
        """
        Generates a block of dead code, which may be:
        - A simple assignment transaction,
        - An unreachable if-block, or
        - An unreachable loop block with a specified loop variable.

        Args:
            var_name (str): Unique identifier for the dead variable.
            loop_var (str): Name to use for loop headers in unreachable loops.
            prefix (str): The indentation to use for the generated code.

        Returns:
            str: A fully formatted block of dead code ending in a newline.
        """
        strategy = self._rng.choice(["assignment", "if_wrap", "loop_wrap"])
        value = self.generate_random_value()

        match strategy:
            case "assignment":
                content = self._build_transaction(var_name, value, prefix)

            case "if_wrap":
                body = self._build_transaction(var_name, value, prefix + self._indent_unit)
                header = self._rng.choice(self._get_opaque_predicates())
                content = self.format_block(header, body, prefix, is_if=True)

            case "loop_wrap":
                body = self._build_transaction(var_name, value, prefix + self._indent_unit)
                raw_header = self._rng.choice(self._get_unreachable_loop_headers())
                header = raw_header.replace("_", loop_var)
                content = self.format_block(header, body, prefix, is_if=False)

            case _:
                # Fallback: treat unknown strategy as a simple assignment
                content = self._build_transaction(var_name, value, prefix)

        # Ensure a single trailing newline
        return content if content.endswith("\n") else content + "\n"

    def _build_transaction(self, var_name: str, value: Any, indent: str) -> str:
        """
        Constructs a multi-line sequence consisting of an assignment,
        an identity modification, and a reference use.

        Args:
            var_name (str): The variable name to manipulate.
            value (Any): The initial value to assign.
            indent (str): The full indentation string to prepend to each line.

        Returns:
            str: A formatted multi-line string of code statements.
        """
        statements = [
            self.get_assignment_statement(var_name, value),
            self._get_meaningless_modification(var_name),
            self._get_fake_use(var_name),
        ]

        return "\n".join(f"{indent}{s}" for s in statements)

    def _get_meaningless_modification(self, var_name: str) -> str:
        """
        Generates an operation that references the variable without changing its state.

        Args:
            var_name (str): The name of the variable to be modified.

        Returns:
            str: An identity operation.
        """
        if self._current_type == "str":
            template = self._rng.choice(self.IDENTITY_OPS_STR)
        else:
            template = self._rng.choice(self.IDENTITY_OPS_NUMERIC)

        return template.replace("{var}", var_name)

    def _get_fake_use(self, var_name: str) -> str:
        """
        Generates a benign statement that references the variable to satisfy
        static analysis tools or avoid "unused variable" warnings.


        Args:
            var_name (str): The variable name to be referenced in the statement.

        Returns:
            str: A single-line statement that consumes the variable without
                affecting program semantics.
        """
        template = self._rng.choice(self.FAKE_USE_PATTERNS)
        return template.replace("{var}", var_name)

    def _get_opaque_predicates(self) -> List[str]:
        """
        Provides boolean expressions that always evaluate to False.

        Returns:
            List[str]: A list of language-specific impossible conditions.
        """
        return self.OPAQUE_PREDICATES

    def _get_unreachable_loop_headers(self) -> List[str]:
        """
        Provides loop headers that will never execute their body.

        Returns:
            List[str]: A list of loop headers.
        """
        return self.UNREACHABLE_LOOP_HEADERS

    # --- Language-Specific Contracts ---

    @abstractmethod
    def get_assignment_statement(self, var_name: str, value: Any) -> str:
        """
        Constructs a single-line variable declaration and assignment.

        Args:
            var_name (str): The unique identifier to be assigned.
            value (Any): The value to assign to the variable.

        Returns:
            str: A language-compliant assignment statement.
        """
        pass

    @abstractmethod
    def format_block(self, header: str, body: str, prefix: str, is_if: bool) -> str:
        """
        Wraps a header and body into a language-specific control block.

        Args:
            header (str): The condition or loop header.
            body (str): The pre-formatted internal statements.
            prefix (str): The indentation for the block header.
            is_if (bool): Indicates if the block is a conditional or a loop.

        Returns:
            str: The fully constructed code block.
        """
        pass

    @abstractmethod
    def generate_random_value(self) -> Any:
        """
        Generates a random value of a type supported by the target language.

        Returns:
            Any: A value valid for an assignment in the concrete language.
        """
        pass

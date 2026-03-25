"""Unit tests for the DeadCodeLexicon abstract base class.

This module verifies:
- The abstract nature of the DeadCodeLexicon (cannot be instantiated).
- Correct behavior of universal raw data generators (int, float, string).
- Logic for building multi-line transactions with consistent indentation.
- Strategy dispatch (assignment vs block wrapping) and string formatting.
- Integration with random seeding for deterministic output.

Testing is performed using a TempLexicon to validate the interface contract
independently of any specific programming language syntax.
"""

import pytest
import random
from typing import List, Any
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.dead_code_lexicon import (
    DeadCodeLexicon,
    INT_MIN,
    INT_MAX,
    FLOAT_MIN,
    FLOAT_MAX,
    FLOAT_PRECISION,
    STR_LENGTH,
)


# ===== Setup =====


class MinimalLexicon(DeadCodeLexicon):
    """Minimal concrete implementation to test base class logic."""

    # --- Populate required class-level lists ---
    OPAQUE_PREDICATES = ["NEVER"]
    UNREACHABLE_LOOP_HEADERS = ["LOOP_ZERO"]
    FAKE_USE_PATTERNS = ["use({var})"]
    IDENTITY_OPS_STR = ["{var} = {var} + ''"]
    IDENTITY_OPS_NUMERIC = ["{var} += 0"]

    def generate_random_value(self) -> Any:
        return "temp_val"

    def get_assignment_statement(self, var_name: str, value: Any) -> str:
        return f"{var_name} := {value}"

    def _get_meaningless_modification(self, var_name: str) -> str:
        return f"modify({var_name})"

    def _get_fake_use(self, var_name: str) -> str:
        return f"use({var_name})"

    def format_block(self, header: str, body: str, prefix: str, is_if: bool) -> str:
        return f"{prefix}BEGIN {header}\n{body}\n{prefix}END"

    def _get_opaque_predicates(self) -> List[str]:
        return ["NEVER"]

    def _get_unreachable_loop_headers(self) -> List[str]:
        return ["LOOP_ZERO"]


@pytest.fixture
def lexicon():
    """Provides a MinimalLexicon instance with a fixed seed for deterministic tests."""
    rng = random.Random(42)
    return MinimalLexicon(rng)


# ===== ABC Enforcement =====


def test_cannot_instantiate_abc():
    """Ensure that the DeadCodeLexicon ABC cannot be instantiated directly."""
    with pytest.raises(TypeError):
        DeadCodeLexicon(random.Random())  # type: ignore[abstract]


# ===== Universal Raw Data Generators =====


def test_raw_int_generation_bounds(lexicon):
    """Verify that integer generation stays within the configured range."""
    results = [lexicon._get_raw_int() for _ in range(50)]
    assert all(INT_MIN <= x <= INT_MAX for x in results)
    assert any(x != results[0] for x in results), "Should show randomness"


def test_raw_float_generation_precision(lexicon):
    """Verify float generation respects range and decimal precision."""
    val = lexicon._get_raw_float()
    assert FLOAT_MIN <= val <= FLOAT_MAX
    # Check that it doesn't exceed configured precision
    decimal_part = str(val).split(".")[-1]
    assert len(decimal_part) <= FLOAT_PRECISION


def test_raw_string_generation_length(lexicon):
    """Verify alphanumeric strings match the configured length."""
    val = lexicon._get_raw_string()
    assert len(val) == STR_LENGTH
    assert val.isalnum()


# ===== Transaction Building =====


def test_build_transaction_logic(lexicon):
    """Verify that a transaction combines assignment, modification, and use with prefix."""
    prefix = "  "
    var = "v1"
    result = lexicon._build_transaction(var, "100", prefix)

    expected_lines = ["  v1 := 100", "  modify(v1)", "  use(v1)"]
    assert result.split("\n") == expected_lines


# ===== Strategy Dispatch and Formatting =====


def test_get_random_dead_code_assignment(lexicon, monkeypatch):
    """Verify output when the 'assignment' strategy is selected."""
    monkeypatch.setattr(lexicon.rng, "choice", lambda x: "assignment")

    output = lexicon.get_random_dead_code("x", "")
    # Should be 3 lines of code plus a trailing newline
    assert len(output.strip().split("\n")) == 3
    assert output.endswith("\n")


def test_get_random_dead_code_if_wrap(lexicon, monkeypatch):
    """Verify block wrapping logic (if_wrap) using the MinimalLexicon's format."""
    # Force the strategy to 'if_wrap' and the header choice to 'NEVER'
    monkeypatch.setattr(lexicon.rng, "choice", lambda x: "if_wrap" if "if_wrap" in x else x[0])

    lexicon.set_indent_unit("TAB")
    output = lexicon.get_random_dead_code("v", "PRE")

    lines = output.strip().split("\n")
    assert lines[0] == "PREBEGIN NEVER"
    assert "PRETABv := temp_val" in lines[1]  # Body must be indented
    assert lines[-1] == "PREEND"


def test_indent_unit_mutation(lexicon):
    """Ensure updating the indent unit affects future block generations."""
    lexicon.set_indent_unit("    ")
    assert lexicon.indent_unit == "    "
    lexicon.set_indent_unit("\t")
    assert lexicon.indent_unit == "\t"


def test_random_dead_code_always_ends_in_newline(lexicon):
    """The generated string must always have exactly one trailing newline for file injection."""
    final_output = lexicon.get_random_dead_code("v", "")
    assert final_output.count("\n") >= 1
    assert final_output[-1] == "\n"
    assert final_output[-2] != "\n"  # No double newlines


def test_get_random_dead_code_loop_wrap(lexicon, monkeypatch):
    """Verify block wrapping logic for loop_wrap strategy."""

    # Force strategy selection to "loop_wrap"
    monkeypatch.setattr(lexicon.rng, "choice", lambda x: "loop_wrap" if "loop_wrap" in x else x[0])

    # Use a visible indent unit to validate propagation
    lexicon.set_indent_unit("  ")
    output = lexicon.get_random_dead_code("v", "P")

    lines = output.strip().split("\n")

    # Header should reflect loop header from _get_unreachable_loop_headers()
    assert lines[0] == "PBEGIN LOOP_ZERO"
    # Body should be indented with prefix + indent_unit
    assert lines[1].startswith("P  v := temp_val")
    # Footer should close the block correctly
    assert lines[-1] == "PEND"


def test_generate_random_value_is_used(monkeypatch):
    """Ensure the value used in generated code comes from generate_random_value."""

    class SpyLexicon(MinimalLexicon):
        def generate_random_value(self):
            # Return a unique sentinel value to detect usage
            return "SENTINEL"

    lex = SpyLexicon(random.Random(1))

    # Force assignment strategy to isolate value usage
    monkeypatch.setattr(lex.rng, "choice", lambda x: "assignment")

    output = lex.get_random_dead_code("x", "")

    # If generate_random_value() is used correctly, SENTINEL must appear
    assert "SENTINEL" in output


def test_opaque_predicates_are_used(monkeypatch):
    """Ensure opaque predicates are consulted during if_wrap."""

    class SpyLexicon(MinimalLexicon):
        def _get_opaque_predicates(self):
            # Provide a unique predicate to verify it is used
            return ["SPECIAL_FALSE"]

    lex = SpyLexicon(random.Random(1))

    # Force if_wrap strategy; subsequent choices pick first element
    monkeypatch.setattr(lex.rng, "choice", lambda x: "if_wrap" if "if_wrap" in x else x[0])

    output = lex.get_random_dead_code("v", "")

    # The custom predicate must appear in the generated block header
    assert "SPECIAL_FALSE" in output


def test_deterministic_output_with_seed():
    """Same seed should produce identical outputs."""

    seed = 123

    # Two independent instances with identical seeds
    lex1 = MinimalLexicon(random.Random(seed))
    lex2 = MinimalLexicon(random.Random(seed))

    out1 = lex1.get_random_dead_code("v", "")
    out2 = lex2.get_random_dead_code("v", "")

    # Determinism is critical for reproducible transformations
    assert out1 == out2


def test_strategy_fallback(monkeypatch, lexicon):
    """Unknown strategy should fallback to assignment behavior."""

    # Inject an invalid strategy to trigger the default match-case branch
    monkeypatch.setattr(lexicon.rng, "choice", lambda x: "unknown_strategy")

    output = lexicon.get_random_dead_code("v", "")
    lines = output.strip().split("\n")

    # Fallback should behave like a plain transaction (3 lines)
    assert len(lines) == 3


def test_block_structure_integrity(lexicon, monkeypatch):
    """Ensure formatted blocks strictly follow header/body/footer structure."""

    # Force if_wrap strategy
    monkeypatch.setattr(lexicon.rng, "choice", lambda x: "if_wrap" if "if_wrap" in x else x[0])

    output = lexicon.get_random_dead_code("v", "X")
    lines = output.strip().split("\n")

    # First line must be a properly prefixed block header
    assert lines[0].startswith("XBEGIN")

    # Last line must be the corresponding block footer
    assert lines[-1] == "XEND"

    # Ensure at least one body line exists between header and footer
    assert len(lines) >= 3


def test_subclass_populates_classvars():
    """Ensure the subclass defines all required class-level lists."""
    lex = MinimalLexicon(random.Random(1))
    for attr in [
        "OPAQUE_PREDICATES",
        "UNREACHABLE_LOOP_HEADERS",
        "FAKE_USE_PATTERNS",
        "IDENTITY_OPS_STR",
        "IDENTITY_OPS_NUMERIC",
    ]:
        val = getattr(lex.__class__, attr, None)
        assert isinstance(val, list) and len(val) > 0, f"{attr} must be populated"

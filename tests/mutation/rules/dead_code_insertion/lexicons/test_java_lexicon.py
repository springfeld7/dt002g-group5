"""Unit tests for the JavaLexicon concrete class.

This module verifies:
- Correct behavior of JavaLexicon random value generators (int, double, String).
- Proper string quoting in assignments.
- Type-safe meaningless modifications.
- Fake variable usage templates.
- Block formatting (if and loop).
- Opaque predicates and unreachable loops integration.
- Strategy dispatch (assignment, if_wrap, loop_wrap) and fallback behavior.
- Deterministic output using seeded RNG.
- Subclass population of required ClassVars.
"""

from numpy import double
import pytest
import random
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.java_lexicon import (
    JavaLexicon,
)


# ===== Fixtures and Helpers =====


@pytest.fixture
def rng():
    """Seeded RNG for deterministic testing."""
    return random.Random(42)


@pytest.fixture
def lexicon(rng):
    """Provides a JavaLexicon instance with deterministic RNG."""
    return JavaLexicon(rng)


# ===== ClassVar Population =====


def test_classvars_populated(lexicon):
    """Ensure all required ClassVars are populated and non-empty."""
    cls = lexicon.__class__
    list_attrs = [
        "OPAQUE_PREDICATES",
        "UNREACHABLE_LOOP_HEADERS",
        "IDENTITY_OPS_STR",
        "IDENTITY_OPS_NUMERIC",
    ]

    for attr in list_attrs:
        val = getattr(cls, attr, None)
        # Check that each required ClassVar is a non-empty list
        assert isinstance(val, list) and len(val) > 0, f"{attr} must be populated as a list"


# ===== Assignment Statement =====


@pytest.mark.parametrize(
    "value,expected",
    [
        ("hello", 'String v = "hello";'),
        ("", 'String v = "";'),
        (123, "int v = 123;"),
        (-1, "int v = -1;"),
        (3.14, "double v = 3.14;"),
    ],
)
def test_get_assignment_statement_quotes(lexicon, value, expected):
    """Strings should be quoted; numbers passed through."""

    # Set _current_type based on value type
    if isinstance(value, str):
        lexicon._current_type = "string"
    elif isinstance(value, int):
        lexicon._current_type = "int"
    else:
        lexicon._current_type = "float"

    stmt = lexicon.get_assignment_statement("v", value)

    # Assert generated assignment matches expected format
    assert stmt == expected


# ===== Meaningless Modifications =====


def test_meaningless_modification_str(lexicon, monkeypatch):
    """For String type, only string identity ops are used."""

    lexicon._current_type = "string"

    # Force choice to pick the first template from IDENTITY_OPS_STR
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: x[0])

    stmt = lexicon._get_meaningless_modification("v")
    # Assert the statement matches one of the string identity templates
    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_STR]


def test_meaningless_modification_numeric(lexicon, monkeypatch):
    """For numeric type, only numeric identity ops are used."""

    lexicon._current_type = "int"

    # Force choice to pick the first template from IDENTITY_OPS_NUMERIC
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: x[0])

    stmt = lexicon._get_meaningless_modification("v")
    # Assert the statement matches one of the numeric identity templates
    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_NUMERIC]


def test_meaningless_modification_type_none(lexicon):
    """_current_type None still returns a numeric template."""

    lexicon._current_type = None

    stmt = lexicon._get_meaningless_modification("v")
    # Numeric templates are used as default fallback
    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_NUMERIC]


# ===== Block Formatting =====


def test_format_block_if(lexicon):
    """format_block prepends 'if ' when is_if is True and missing."""

    body = "  stmt"
    result = lexicon.format_block("cond", body, "", is_if=True)
    # Header should start with 'if (cond) {' and body appended
    assert result.startswith("if (cond) {\n") and body in result


def test_format_block_loop(lexicon):
    """format_block leaves loop header untouched when is_if=False."""
    body = "  stmt"
    result = lexicon.format_block("while(false)", body, "", is_if=False)
    assert result.startswith("while(false) {") and body in result


# ===== Opaque Predicates & Loop Headers =====


def test_opaque_predicates_list(lexicon):
    """_get_opaque_predicates returns non-empty list matching class variable."""

    preds = lexicon._get_opaque_predicates()
    assert isinstance(preds, list) and preds == lexicon.OPAQUE_PREDICATES


def test_unreachable_loop_headers_list(lexicon):
    """_get_unreachable_loop_headers returns non-empty list matching class variable."""

    loops = lexicon._get_unreachable_loop_headers()
    assert isinstance(loops, list) and loops == lexicon.UNREACHABLE_LOOP_HEADERS


# ===== Integration: get_random_dead_code =====


def test_get_random_dead_code_assignment(monkeypatch, lexicon):
    """Assignment strategy returns a short transaction ending with newline."""

    # Force RNG to select "assignment" strategy
    monkeypatch.setattr(
        lexicon._rng, "choice", lambda x: "assignment" if "assignment" in x else x[0]
    )

    output = lexicon.get_random_dead_code("v", "i", "")
    lines = output.strip().split("\n")

    # Output should be exactly 2 lines: assignment + modification
    assert len(lines) == 2
    # Output should end with newline
    assert output.endswith("\n")


def test_get_random_dead_code_if_wrap(monkeypatch, lexicon):
    """If_wrap strategy formats header/body correctly with proper indentation."""

    # Force RNG to always select 'if_wrap' strategy
    def fake_choice(options):
        if "if_wrap" in options:
            return "if_wrap"
        # fallback for opaque predicate selection
        return options[0]

    monkeypatch.setattr(lexicon._rng, "choice", fake_choice)

    # Use 2-space indentation
    lexicon.set_indent_unit("  ")

    output = lexicon.get_random_dead_code("v", "i", "")

    # Remove any trailing empty lines
    lines = [line for line in output.split("\n") if line.strip() != ""]

    # The first line must be the 'if' header
    assert lines[0].startswith("if ")

    # The last line is the closing brace
    assert lines[-1].strip() == "}"

    # The body lines are everything in between
    body_lines = lines[1:-1]
    assert len(body_lines) >= 2  # at least assignment + identity operation

    # Each body line must start with the indent
    for line in body_lines:
        assert line.startswith("  ")


def test_get_random_dead_code_loop_wrap(monkeypatch, lexicon):
    """Loop_wrap strategy formats header/body/footer correctly."""

    # Force RNG to select 'loop_wrap' strategy
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: "loop_wrap" if "loop_wrap" in x else x[0])

    lexicon.set_indent_unit("  ")

    output = lexicon.get_random_dead_code("v", "i", "Q")
    lines = output.strip().split("\n")

    # Header should start with 'Q'
    assert lines[0].startswith("Q")
    # Body lines should contain variable 'v'
    assert any("v" in line for line in lines[1:])
    # Footer line must exist
    assert lines[-1]


def test_get_random_dead_code_fallback(monkeypatch, lexicon):
    """Unknown strategy falls back to assignment."""

    # Force RNG to an unknown strategy to trigger fallback
    monkeypatch.setattr(
        lexicon._rng,
        "choice",
        lambda x: "unknown" if isinstance(x, list) and "assignment" in x else x[0],
    )

    output = lexicon.get_random_dead_code("v", "i", "")
    lines = output.strip().split("\n")
    # Fallback should produce 2-line transaction
    assert len(lines) == 2


# ===== Deterministic RNG Behavior =====


def test_deterministic_output_with_seed():
    """Same seed produces identical outputs."""

    seed = 999
    lex1 = JavaLexicon(random.Random(seed))
    lex2 = JavaLexicon(random.Random(seed))

    out1 = lex1.get_random_dead_code("v", "i", "")
    out2 = lex2.get_random_dead_code("v", "i", "")

    # Outputs should match exactly
    assert out1 == out2


# ===== Edge Cases =====


def test_assignment_negative_number(lexicon):
    """Assigning negative number works as expected."""

    lexicon._current_type = "int"
    stmt = lexicon.get_assignment_statement("v", -123)
    # Negative number assignment should be correct
    assert stmt == "int v = -123;"


def test_meaningless_modification_multiple_choices(monkeypatch, lexicon):
    """All templates are selectable for String type."""

    lexicon._current_type = "string"
    choices = []
    templates = lexicon.IDENTITY_OPS_STR
    idx = 0

    # Cycle through all templates to verify each can be selected
    def fake_choice(lst):
        nonlocal idx
        val = lst[idx % len(lst)]
        idx += 1
        return val

    monkeypatch.setattr(lexicon._rng, "choice", fake_choice)
    for _ in range(len(templates)):
        choices.append(lexicon._get_meaningless_modification("v"))

    # All templates must have been chosen at least once
    assert set(choices) == set(t.format(var="v") for t in templates)


def test_loop_var_replacement_in_header(monkeypatch, lexicon):
    """Ensure that {var} in UNREACHABLE_LOOP_HEADERS is replaced with loop_var."""

    loop_header = "for(int {var} = 0; {var} < 0; ++{var})"

    # Custom choice function to control RNG outputs
    def fake_choice(lst):
        if "loop_wrap" in lst:
            return "loop_wrap"
        elif lst == lexicon.UNREACHABLE_LOOP_HEADERS:
            return loop_header
        else:
            return lst[0]

    monkeypatch.setattr(lexicon._rng, "choice", fake_choice)
    lexicon.set_indent_unit("")
    loop_var = "my_loop"

    output = lexicon.get_random_dead_code("v", loop_var, "")
    header_line = output.splitlines()[0]
    # Ensure loop_var replaced correctly
    assert loop_var in header_line
    assert "{var}" not in header_line

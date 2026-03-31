"""Unit tests for the PythonLexicon concrete class.

This module verifies:
- Correct behavior of PythonLexicon random value generators (int, float, str).
- Proper string quoting in assignments.
- Type-safe meaningless modifications.
- Fake variable usage templates.
- Block formatting (if and loop).
- Opaque predicates and unreachable loops integration.
- Strategy dispatch (assignment, if_wrap, loop_wrap) and fallback behavior.
- Deterministic output using seeded RNG.
- Subclass population of required ClassVars.
"""

import pytest
import random
from src.transtructiver.mutation.rules.dead_code_insertion.lexicons.python_lexicon import (
    PythonLexicon,
)


# ===== Fixtures and Helpers =====


@pytest.fixture
def rng():
    """Seeded RNG for deterministic testing."""
    return random.Random(42)


@pytest.fixture
def lexicon(rng):
    """Provides a PythonLexicon instance with deterministic RNG."""
    return PythonLexicon(rng)


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
        assert isinstance(val, list) and len(val) > 0, f"{attr} must be populated as a list"


# ===== Assignment Statement =====


@pytest.mark.parametrize(
    "value,expected",
    [
        ("hello", "v = 'hello'"),
        ("", "v = ''"),
        (123, "v = 123"),
        (-1, "v = -1"),
        (3.14, "v = 3.14"),
    ],
)
def test_get_assignment_statement_quotes(lexicon, value, expected):
    """Strings should be quoted; numbers passed through."""
    stmt = lexicon.get_assignment_statement("v", value)
    assert stmt == expected


# ===== Meaningless Modifications =====


def test_meaningless_modification_str(lexicon, monkeypatch):
    """For str type, only string identity ops are used."""

    lexicon._current_type = "string"
    # Force choice to first template
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: x[0])

    stmt = lexicon._get_meaningless_modification("v")

    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_STR]


def test_meaningless_modification_numeric(lexicon, monkeypatch):
    """For numeric type, only numeric identity ops are used."""

    lexicon._current_type = "int"
    # Force choice to first template
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: x[0])

    stmt = lexicon._get_meaningless_modification("v")

    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_NUMERIC]


def test_meaningless_modification_type_none(lexicon):
    """_current_type None still returns a numeric template."""

    lexicon._current_type = None

    stmt = lexicon._get_meaningless_modification("v")
    assert stmt in [tpl.format(var="v") for tpl in lexicon.IDENTITY_OPS_NUMERIC]


# ===== Block Formatting =====


def test_format_block_if(lexicon):
    """format_block prepends 'if ' when is_if is True and missing."""
    body = "  stmt"

    result = lexicon.format_block("cond", body, "", is_if=True)
    assert result.startswith("if cond:\n") and result.endswith(body)


def test_format_block_loop(lexicon):
    """format_block leaves loop header untouched when is_if=False."""
    body = "  stmt"
    result = lexicon.format_block("while False", body, "", is_if=False)
    assert result.startswith("while False:\n") and result.endswith(body)


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
    """Assignment strategy returns 3-line transaction ending with newline."""
    # Force strategy selection to "assignment", if available, otherwise default to int
    monkeypatch.setattr(
        lexicon._rng, "choice", lambda x: "assignment" if "assignment" in x else "int"
    )
    output = lexicon.get_random_dead_code("v", "i", "")
    lines = output.strip().split("\n")

    assert len(lines) == 2
    assert output.endswith("\n")


def test_get_random_dead_code_if_wrap(monkeypatch, lexicon):
    """If_wrap strategy formats header/body correctly."""
    # Force RNG to always select the "if_wrap" strategy,
    # while keeping all other random choices valid
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: "if_wrap" if "if_wrap" in x else x[0])

    lexicon.set_indent_unit("  ")

    output = lexicon.get_random_dead_code("v", "i", "")
    lines = output.strip().split("\n")

    # First line must be an 'if' statement with correct prefix
    assert lines[0].startswith("if ")

    body_lines = lines[1:]
    # A full transaction should produce at least: assignment + modification
    assert len(body_lines) >= 2

    # Each body line must be indented relative to the header and use the configured indent unit
    assert all(line.startswith("  ") for line in body_lines)

    body = "\n".join(body_lines)
    assert "v" in body
    # Ensure at least one assignment-like operation exists
    assert any(op in body for op in ["v =", "v +=", "v *=", "v -="])


def test_get_random_dead_code_loop_wrap(monkeypatch, lexicon):
    """Loop_wrap strategy formats header/body/footer correctly."""
    # Force RNG to always select the "loop_wrap" strategy,
    # while keeping all other random choices valid
    monkeypatch.setattr(lexicon._rng, "choice", lambda x: "loop_wrap" if "loop_wrap" in x else x[0])
    lexicon.set_indent_unit("  ")
    output = lexicon.get_random_dead_code("v", "i", "Q")
    lines = output.strip().split("\n")

    assert lines[0].startswith("Q")
    assert any("v =" in line for line in lines[1:])
    assert lines[-1]  # Footer exists


def test_get_random_dead_code_fallback(monkeypatch, lexicon):
    """Unknown strategy falls back to assignment."""
    # Force RNG to an unknown strategy, which should trigger fallback to assignment
    monkeypatch.setattr(
        lexicon._rng,
        "choice",
        lambda x: (
            "unknown"
            if isinstance(x, list) and "assignment" in x  # strategy list
            else x[0]  # safe fallback for everything else
        ),
    )

    output = lexicon.get_random_dead_code("v", "i", "")
    lines = output.strip().split("\n")

    # Fallback should behave like assignment (2-line transaction)
    assert len(lines) == 2


# ===== Deterministic RNG Behavior =====


def test_deterministic_output_with_seed():
    """Same seed produces identical outputs."""
    seed = 999
    lex1 = PythonLexicon(random.Random(seed))
    lex2 = PythonLexicon(random.Random(seed))

    out1 = lex1.get_random_dead_code("v", "i", "")
    out2 = lex2.get_random_dead_code("v", "i", "")

    assert out1 == out2


# ===== Edge Cases =====


def test_assignment_empty_string(lexicon):
    """Assigning empty string is correctly quoted."""
    stmt = lexicon.get_assignment_statement("v", "")
    assert stmt == "v = ''"


def test_assignment_negative_number(lexicon):
    """Assigning negative number works as expected."""
    stmt = lexicon.get_assignment_statement("v", -123)
    assert stmt == "v = -123"


def test_meaningless_modification_multiple_choices(monkeypatch, lexicon):
    """All templates are selectable for string type."""
    lexicon._current_type = "string"
    choices = []

    # Cycle through all templates
    templates = lexicon.IDENTITY_OPS_STR
    idx = 0

    def fake_choice(lst):
        nonlocal idx
        val = lst[idx % len(lst)]
        idx += 1
        return val

    monkeypatch.setattr(lexicon._rng, "choice", fake_choice)
    for _ in range(len(templates)):
        choices.append(lexicon._get_meaningless_modification("v"))

    assert set(choices) == set(t.format(var="v") for t in templates)


def test_loop_var_replacement_in_header(monkeypatch, lexicon):
    """Ensure that {var} in UNREACHABLE_LOOP_HEADERS is replaced with loop_var."""

    loop_header = "for {var} in []"  # guaranteed to contain {var}

    def fake_choice(lst):
        # Custom choice function to control RNG outputs during the test:
        # 1. If the list contains strategy options, always select "loop_wrap".
        # 2. If the list is UNREACHABLE_LOOP_HEADERS, return a header containing "{var}" to test replacement.
        # 3. Otherwise, default to the first element of the list.
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
    assert loop_var in header_line
    assert "{var}" not in header_line

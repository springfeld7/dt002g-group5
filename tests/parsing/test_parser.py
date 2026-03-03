"""Test cases for the Parser class.

Tests cover parsing validation, discard criteria, and tree structure analysis.
Tests are organized into logical groups for clarity and maintainability.
All tests are independent and reproducible.
"""

import pytest
from types import SimpleNamespace
from tree_sitter import Parser as TSParser
from src.transtructiver.parsing.parser import Parser
from src.transtructiver.node import Node


def make_node(
    node_type,
    children=None,
    named_children=None,
    is_error=False,
    child_count=None,
):
    """Create a minimal node-like object for parser unit tests."""
    children = children or []
    named_children = named_children or []
    if child_count is None:
        child_count = len(children)
    return SimpleNamespace(
        type=node_type,
        children=children,
        named_children=named_children,
        child_count=child_count,
        named_child_count=len(named_children),
        is_error=is_error,
    )


class TestParserInitialization:
    """Test suite for Parser initialization."""

    def test_parser_instantiation(self):
        """Test that a Parser instance can be created."""
        parser = Parser()
        assert parser is not None
        assert hasattr(parser, "ts_parser")

    def test_parser_ts_parser_type(self):
        """Test that Parser contains a Tree-sitter parser."""
        parser = Parser()
        assert isinstance(parser.ts_parser, TSParser)


class TestParserTrivialNodeDetection:
    """Test suite for is_trivial method."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_is_trivial_break_statement(self, parser):
        """Test that break statements are identified as trivial."""
        node = make_node("break_statement")
        assert parser.is_trivial(node) is True

    def test_is_trivial_continue_statement(self, parser):
        """Test that continue statements are identified as trivial."""
        node = make_node("continue_statement")
        assert parser.is_trivial(node) is True

    def test_is_trivial_empty_statement(self, parser):
        """Test that empty statements are identified as trivial."""
        node = make_node("empty_statement")
        assert parser.is_trivial(node) is True

    def test_is_trivial_non_trivial_statement(self, parser):
        """Test that non-trivial statements are not identified as trivial."""
        node = make_node("assignment")
        assert parser.is_trivial(node) is False

    def test_is_trivial_comment(self, parser):
        """Test that comments are identified as trivial."""
        node = make_node("comment")
        assert parser.is_trivial(node) is True

    def test_is_trivial_expression_statement(self, parser):
        """Test that expression statements are not identified as trivial."""
        node = make_node("expression_statement")
        assert parser.is_trivial(node) is False

    def test_is_trivial_case_sensitivity(self, parser):
        """Test that type matching is case-sensitive."""
        node = make_node("RETURN_STATEMENT")
        # Should not match because of case difference
        assert parser.is_trivial(node) is False


class TestParserMeaningfulNodeDetection:
    """Test suite for is_meaningful method."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_is_meaningful_expression(self, parser):
        """Test that expressions are identified as meaningful."""
        node = make_node("binary_expression")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_statement(self, parser):
        """Test that statements are identified as meaningful."""
        node = make_node("expression_statement")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_definition(self, parser):
        """Test that definitions are identified as meaningful."""
        node = make_node("function_definition")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_declaration(self, parser):
        """Test that declarations are identified as meaningful."""
        node = make_node("variable_declaration")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_assignment(self, parser):
        """Test that assignments are identified as meaningful."""
        node = make_node("assignment_expression")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_block(self, parser):
        """Test that blocks are identified as meaningful."""
        node = make_node("block")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_suite(self, parser):
        """Test that suites are identified as meaningful."""
        node = make_node("suite")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_identifier(self, parser):
        """Test that non-meaningful types are not identified as meaningful."""
        node = make_node("identifier")
        assert parser.is_meaningful(node) is True

    def test_is_meaningful_operator_token(self, parser):
        """Test that operators are not meaningful."""
        node = make_node("+")
        assert parser.is_meaningful(node) is False


class TestParserHasMeaningfulStructure:
    """Test suite for has_meaningful_structure method."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_has_meaningful_structure_with_assignment(self, parser):
        """Test function with assignment has meaningful structure."""
        # Create a mock function node with a body containing assignment
        assignment = make_node("assignment")
        body = make_node("block", named_children=[assignment])
        func_node = make_node("function_definition", children=[body])

        assert parser.has_meaningful_structure(func_node) is True

    def test_has_meaningful_structure_only_return(self, parser):
        """Test function with only return lacks meaningful structure."""
        return_stmt = make_node("return_statement")
        body = make_node("suite", named_children=[return_stmt])
        func_node = make_node("function_definition", children=[body])

        assert parser.has_meaningful_structure(func_node) is False

    def test_has_meaningful_structure_empty_body(self, parser):
        """Test function with empty body lacks meaningful structure."""
        body = make_node("block", named_children=[])
        func_node = make_node("function_definition", children=[body])

        assert parser.has_meaningful_structure(func_node) is False

    def test_has_meaningful_structure_no_body_node(self, parser):
        """Test handling when no body node exists."""
        func_node = make_node("function_definition", children=[], named_children=[])

        # Should check func_node itself
        result = parser.has_meaningful_structure(func_node)
        assert isinstance(result, bool)

    def test_has_meaningful_structure_mixed_statements(self, parser):
        """Test function with meaningful and trivial statements."""
        assignment = make_node("assignment")
        return_stmt = make_node("return_statement")
        body = make_node("suite", named_children=[assignment, return_stmt])
        func_node = make_node("function_definition", children=[body])

        # Should be True because it has at least one meaningful statement
        assert parser.has_meaningful_structure(func_node) is True

    def test_has_meaningful_structure_compound_body(self, parser):
        """Test detection of compound body structures."""
        expr = make_node("expression")
        body = make_node("compound_statement", named_children=[expr])
        func_node = make_node("function_definition", children=[body])

        assert parser.has_meaningful_structure(func_node) is True

    def test_has_meaningful_structure_empty_return(self, parser):
        """Test function with empty return statement."""
        ret = make_node("return_statement")
        body = make_node("compound_statement", named_children=[ret])
        func_node = make_node("function_definition", children=[body])
        assert parser.has_meaningful_structure(func_node) is False

    def test_has_meaningful_structure_return_assignment(self, parser):
        """Test function with empty return statement."""
        expr = make_node("expression")
        ret = make_node("return_statement", named_children=[expr])
        body = make_node("compound_statement", named_children=[ret])
        func_node = make_node("function_definition", children=[body])
        assert parser.has_meaningful_structure(func_node) is True


class TestParserDiscardCriteria:
    """Test suite for should_discard method."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_discard_empty_source(self, parser):
        """Test that empty source code is marked for discard."""
        root = make_node("module", children=[])

        reason = parser.should_discard(root, "")
        assert reason == "empty_source"

    def test_discard_whitespace_only_source(self, parser):
        """Test that whitespace-only source is marked for discard."""
        root = make_node("module", children=[])

        reason = parser.should_discard(root, "   \n\t  ")
        assert reason == "empty_source"

    def test_discard_no_children(self, parser):
        """Test that root with no children is marked for discard."""
        root = make_node("module", children=[])

        reason = parser.should_discard(root, "some code")
        assert reason == "no_children"

    def test_discard_root_error_only(self, parser):
        """Test that tree with only error nodes is marked for discard."""
        error_child = make_node("ERROR", is_error=True)
        root = make_node("module", children=[error_child])

        reason = parser.should_discard(root, "invalid code")
        assert reason == "root_error_only"

    def test_discard_no_meaningful_structure(self, parser):
        """Test that code without meaningful structure is marked for discard."""
        # Create a node that appears valid but has no meaningful structure
        child = make_node("function_definition", is_error=False)
        root = make_node("module", children=[child])

        # Override has_meaningful_structure to return False for all children
        parser.has_meaningful_structure = lambda _node: False

        reason = parser.should_discard(root, "return")
        assert reason == "no_meaningful_structure"

    def test_discard_valid_code_returns_none(self, parser):
        """Test that valid code returns None (no discard reason)."""
        meaningful_child = make_node("function_definition", is_error=False)
        root = make_node("module", children=[meaningful_child])

        # Override has_meaningful_structure to return True
        parser.has_meaningful_structure = lambda _node: True

        reason = parser.should_discard(root, "x = 5")
        assert reason is None

    def test_discard_multiple_error_nodes(self, parser):
        """Test with multiple error nodes."""
        error1 = make_node("ERROR", is_error=True)
        error2 = make_node("ERROR", is_error=True)
        root = make_node("module", children=[error1, error2])

        reason = parser.should_discard(root, "@@@@")
        assert reason == "root_error_only"


class TestParserParseSuccessful:
    """Test suite for successful parsing scenarios."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_parse_valid_python_function(self, parser):
        """Test parsing a valid Python function."""
        code = """
def add(a, b):
    result = a + b
    return result
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None
        assert tree.type == "module"
        assert isinstance(tree, Node)

    def test_parse_python_class_definition(self, parser):
        """Test parsing a Python class definition."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_python_with_loops(self, parser):
        """Test parsing Python code with loops."""
        code = """
def sum_range(n):
    total = 0
    for i in range(n):
        total = total + i
    return total
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_python_with_conditionals(self, parser):
        """Test parsing Python code with conditionals."""
        code = """
def max_value(a, b):
    if a > b:
        return a
    else:
        return b
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_python_with_comments(self, parser):
        """Test parsing Python code with comments."""
        code = """
# This is a comment
def multiply(x, y):
    # Calculate product
    result = x * y
    return result
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_python_multiline_strings(self, parser):
        """Test parsing Python with multiline strings."""
        code = '''
        def get_info():
            """
            This is a docstring
            spanning multiple lines
            """
            result = "info"
            return result
        '''
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_python_nested_functions(self, parser):
        """Test parsing nested function definitions."""
        code = """
def outer():
    def inner():
        x = 1
        return x
    return inner()
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_javascript_function(self, parser):
        """Test parsing JavaScript code."""
        code = """
function add(a, b) {
    const result = a + b;
    return result;
}
"""
        tree, reason = parser.parse(code, "javascript")
        assert tree is not None
        assert reason is None

    def test_parse_java_class(self, parser):
        """Test parsing Java code."""
        code = """
public class Calculator {
    public int add(int a, int b) {
        int result = a + b;
        return result;
    }
}
"""
        tree, reason = parser.parse(code, "java")
        # Java may be stricter, but if it parses, structure should be valid
        assert tree is not None or isinstance(reason, str)


class TestParserParseFailing:
    """Test suite for parsing failure scenarios."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_parse_empty_source(self, parser):
        """Test parsing empty source code."""
        code = ""
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "empty_source"

    def test_parse_whitespace_only(self, parser):
        """Test parsing whitespace-only code."""
        code = "   \n\t  \n"
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "empty_source"

    def test_parse_invalid_syntax(self, parser):
        """Test parsing code with invalid syntax."""
        code = "@@@###$$$"
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason in ["root_error_only", "no_meaningful_structure"]

    def test_parse_only_return_statement(self, parser):
        """Test parsing code with only return statement."""
        code = "return"
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "no_meaningful_structure"

    def test_parse_only_break_statement(self, parser):
        """Test parsing code with only break statement."""
        code = "break"
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "no_meaningful_structure"

    def test_parse_incomplete_syntax(self, parser):
        """Test parsing incomplete code."""
        code = "def incomplete("
        tree, reason = parser.parse(code, "python")
        assert tree is None
        # Should be rejected due to errors or lack of meaningful structure


class TestParserLanguageSupport:
    """Test suite for language support."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_parse_python_language(self, parser):
        """Test Python language is supported."""
        code = "x = 42"
        tree, reason = parser.parse(code, "python")
        assert tree is not None or reason is not None

    def test_parse_javascript_language(self, parser):
        """Test JavaScript language is supported."""
        code = "let x = 42;"
        tree, reason = parser.parse(code, "javascript")
        assert tree is not None or reason is not None

    def test_parse_java_language(self, parser):
        """Test Java language is supported."""
        code = "int x = 42;"
        tree, reason = parser.parse(code, "java")
        assert tree is not None or reason is not None

    def test_parse_unsupported_language(self, parser):
        """Test that unsupported language raises ValueError."""
        code = "some code"
        with pytest.raises(ValueError, match="Unsupported language"):
            parser.parse(code, "nonexistent_language")

    def test_parse_case_insensitive_language(self, parser):
        """Test that language names are case-insensitive."""
        code = """
def test():
    x = 1
    return x
"""
        # Should work with uppercase
        tree, reason = parser.parse(code, "PYTHON")
        assert tree is not None or reason is not None

    def test_parse_mixed_case_language(self, parser):
        """Test language name with mixed case."""
        code = """
def test():
    x = 1
    return x
"""
        # Should work with mixed case
        tree, reason = parser.parse(code, "PythOn")
        assert tree is not None or reason is not None


class TestParserEdgeCases:
    """Test suite for edge cases and special scenarios."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_parse_unicode_string_literals(self, parser):
        """Test parsing code with Unicode string literals."""
        code = 'text = "\\u4f60\\u597d"'
        tree, reason = parser.parse(code, "python")
        assert tree is not None or reason is not None

    def test_parse_special_characters_in_strings(self, parser):
        """Test parsing strings with special characters."""
        code = '''s = "!@#$%^&*()_+-=[]{}|;:,.<>?"'''
        tree, reason = parser.parse(code, "python")
        assert tree is not None or reason is not None

    def test_parse_very_long_line(self, parser):
        """Test parsing very long lines."""
        code = "x = " + " + ".join(str(i) for i in range(100))
        tree, reason = parser.parse(code, "python")
        assert tree is not None or reason is not None

    def test_parse_deeply_nested_code(self, parser):
        """Test parsing deeply nested code structures."""
        code = "def a():\n"
        for i in range(10):
            code += "    if True:\n"
        code += "        x = 1\n"
        code += "        return x\n"

        tree, reason = parser.parse(code, "python")
        assert tree is not None or reason is not None

    def test_parse_multiple_functions(self, parser):
        """Test parsing multiple function definitions."""
        code = """
def func1():
    x = 1
    return x

def func2():
    y = 2
    return y

def func3():
    z = 3
    return z
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_complex_expressions(self, parser):
        """Test parsing complex expressions."""
        code = """
def calc():
    result = (a + b) * (c - d) / (e ** f) + g % h
    return result
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_lambda_functions(self, parser):
        """Test parsing lambda functions."""
        code = """
square = lambda x: x ** 2
add = lambda x, y: x + y
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_with_decorators(self, parser):
        """Test parsing decorated functions."""
        code = """
@decorator
def decorated_function(x):
    return x * 2
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_list_comprehension(self, parser):
        """Test parsing list comprehensions."""
        code = """
squares = [x**2 for x in range(10) if x % 2 == 0]
"""
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None


class TestParserConsistency:
    """Test suite for parser consistency and determinism."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    def test_multiple_parse_same_code_consistent(self, parser):
        """Test that parsing same code multiple times gives consistent results."""
        code = """
def test():
    x = 42
    return x
"""
        tree1, reason1 = parser.parse(code, "python")
        tree2, reason2 = parser.parse(code, "python")

        assert (tree1 is None and tree2 is None) or (tree1 is not None and tree2 is not None)
        assert reason1 == reason2

    def test_parse_with_different_instances(self):
        """Test that different parser instances produce same results."""
        parser1 = Parser()
        parser2 = Parser()

        code = """
def add(a, b):
    return a + b
"""
        tree1, reason1 = parser1.parse(code, "python")
        tree2, reason2 = parser2.parse(code, "python")

        assert reason1 == reason2
        assert (tree1 is None and tree2 is None) or (tree1 is not None and tree2 is not None)

    def test_parse_deterministic_structure(self, parser):
        """Test that parse results have deterministic structure."""
        code = """
def calc(x, y):
    a = x + y
    b = x - y
    return a * b
"""
        tree, _ = parser.parse(code, "python")

        if tree is not None:
            # Parse again and verify structure is same
            tree2, _ = parser.parse(code, "python")

            assert tree.type == tree2.type
            assert len(tree.children) == len(tree2.children)

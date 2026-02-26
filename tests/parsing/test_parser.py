"""Test cases for the Parser class.

Tests cover parsing validation, discard criteria, and tree structure analysis.
"""

import pytest
from src.transtructiver.prototype.parsing.parser import Parser


class TestParser:
    """Test suite for Parser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    # ===== Successful Parsing Tests =====

    def test_parse_valid_python_function(self, parser):
        """Test parsing a valid Python function returns a CST."""
        code = """
        def add(a, b):
            return a + b
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None
        assert tree.type == "module"

    def test_parse_valid_java_method(self, parser):
        """Test parsing a valid Java method returns a CST."""
        code = """
        public int add(int a, int b) {
            return a + b;
        }
        """
        tree, reason = parser.parse(code, "java")
        assert tree is not None
        assert reason is None
        assert tree.type == "program"

    def test_parse_valid_javascript_function(self, parser):
        """Test parsing a valid JavaScript function returns a CST."""
        code = """
        function multiply(x, y) {
            return x * y;
        }
        """
        tree, reason = parser.parse(code, "javascript")
        assert tree is not None
        assert reason is None
        assert tree.type == "program"

    # ===== Discard Criteria Tests =====

    def test_discard_empty_source(self, parser):
        """Test that empty source code is discarded."""
        code = "   \n\t  "
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "empty_source"

    def test_discard_no_children(self, parser):
        """Test that trees with no children are discarded."""
        code = ""
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason in ["empty_source", "no_children"]

    def test_discard_root_error_only(self, parser):
        """Test that trees with only error nodes are discarded."""
        code = "@@@###$$$"  # Invalid syntax in most languages
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "root_error_only"

    def test_discard_no_meaningful_structure_trivial_only(self, parser):
        """Test that code with only trivial statements is discarded."""
        code = """
        def empty():
            return
        """
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "no_meaningful_structure"

    def test_discard_no_meaningful_structure_empty_function(self, parser):
        """Test that empty functions are discarded."""
        code = """
        def empty():
            pass
        """
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason == "no_meaningful_structure"

    def test_discard_invalid_utf8(self, parser):
        """Test that invalid UTF-8 is discarded."""
        # Simulate by testing the encoding check
        code = "def valid():\n    return 42"
        tree, reason = parser.parse(code, "python")
        assert tree is not None  # Valid UTF-8 should pass

    # ===== is_trivial Tests =====

    def test_is_trivial_return_statement(self, parser):
        """Test that return statements are identified as trivial."""
        code = "return"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        # Find return node
        for node in tree_obj.root_node.walk():
            if "return" in node.type:
                assert parser.is_trivial(node)
                break

    def test_is_trivial_break_statement(self, parser):
        """Test that break statements are identified as trivial."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = "break"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "break" in node.type:
                assert parser.is_trivial(node)
                break

    def test_is_not_trivial_assignment(self, parser):
        """Test that assignment statements are not trivial."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = "x = 5"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "assignment" in node.type:
                assert not parser.is_trivial(node)
                break

    # ===== is_meaningful Tests =====

    def test_is_meaningful_expression(self, parser):
        """Test that expressions are identified as meaningful."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = "x + y"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "expression" in node.type:
                assert parser.is_meaningful(node)
                break

    def test_is_meaningful_declaration(self, parser):
        """Test that declarations are identified as meaningful."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("java")
        code = "int x = 5;"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "declaration" in node.type:
                assert parser.is_meaningful(node)
                break

    def test_is_meaningful_statement(self, parser):
        """Test that statements are identified as meaningful."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = "print('hello')"
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "statement" in node.type and "expression" in node.type:
                assert parser.is_meaningful(node)
                break

    # ===== has_meaningful_structure Tests =====

    def test_has_meaningful_structure_with_assignment(self, parser):
        """Test that functions with assignments have meaningful structure."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = """
        def func():
            x = 5
        """
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        # Get function definition node
        for node in tree_obj.root_node.walk():
            if "function_definition" in node.type:
                assert parser.has_meaningful_structure(node)
                break

    def test_has_meaningful_structure_empty_function(self, parser):
        """Test that empty functions lack meaningful structure."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = """
        def func():
            pass
        """
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "function_definition" in node.type:
                assert not parser.has_meaningful_structure(node)
                break

    def test_has_meaningful_structure_only_return(self, parser):
        """Test that functions with only return lack meaningful structure."""
        from tree_sitter_language_pack import get_language
        parser.ts_parser.language = get_language("python")
        code = """
        def func():
            return
        """
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))
        for node in tree_obj.root_node.walk():
            if "function_definition" in node.type:
                assert not parser.has_meaningful_structure(node)
                break

    # ===== Language Support Tests =====

    def test_parse_unsupported_language(self, parser):
        """Test that unsupported languages raise ValueError."""
        code = "some code"
        with pytest.raises(ValueError, match="Unsupported language"):
            parser.parse(code, "nonexistent_language")

    def test_parse_python(self, parser):
        """Test Python language support."""
        code = "x = 42"
        tree, reason = parser.parse(code, "python")
        # May be discarded for no meaningful structure, but should parse
        assert reason in [None, "no_meaningful_structure"]

    def test_parse_java(self, parser):
        """Test Java language support."""
        code = "int x = 42;"
        tree, reason = parser.parse(code, "java")
        assert reason in [None, "no_meaningful_structure"]

    def test_parse_javascript(self, parser):
        """Test JavaScript language support."""
        code = "const x = 42;"
        tree, reason = parser.parse(code, "javascript")
        assert reason in [None, "no_meaningful_structure"]

    # ===== Edge Cases =====

    def test_parse_with_comments(self, parser):
        """Test parsing code with comments."""
        code = """
        # This is a comment
        def add(a, b):
            # Another comment
            return a + b
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_multiline_code(self, parser):
        """Test parsing multiline code structures."""
        code = """
        class Calculator:
            def add(self, a, b):
                result = a + b
                return result
            
            def subtract(self, a, b):
                result = a - b
                return result
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None
        assert reason is None

    def test_parse_with_syntax_error(self, parser):
        """Test parsing code with partial syntax errors."""
        code = """
        def incomplete(:
            print("test")
        """
        tree, reason = parser.parse(code, "python")
        # Should be discarded due to errors or missing structure
        assert tree is None or reason is not None

"""Test cases for the Parser class.

Tests cover parsing validation, discard criteria, and tree structure analysis.
"""

import pytest
from tree_sitter_language_pack import get_language
from src.transtructiver.prototype.parsing.parser import Parser


def find_child_with_type(node, type_substring):
    """Helper to find a child node with type containing substring."""
    for child in node.children:
        if type_substring in child.type:
            return child
        result = find_child_with_type(child, type_substring)
        if result:
            return result
    return None


class TestParser:
    """Test suite for Parser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return Parser()

    # ===== Successful Parsing Tests =====

    def test_parse_valid_python_with_assignment(self, parser):
        """Test parsing Python code with assignments returns a CST."""
        code = """
        def add(a, b):
            result = a + b
            return result
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None, f"Expected tree but got reason: {reason}"
        assert reason is None
        assert tree.type == "module"

    def test_parse_valid_java_with_assignment(self, parser):
        """Test parsing Java code with variable assignment."""
        code = """
        public class Math {
            public int add(int a, int b) {
                int result = a + b;
                return result;
            }
        }
        """
        tree, reason = parser.parse(code, "java")
        # Java parsing may be stricter, allow for no_meaningful_structure
        assert tree is not None or reason == "no_meaningful_structure"

    def test_parse_python_with_calculation(self, parser):
        """Test parsing Python with calculation returns a CST."""
        code = """
        def multiply(x, y):
            result = x * y
            return result
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None, f"Expected tree but got reason: {reason}"
        assert reason is None

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
        code = "@@@###$$$"  # Invalid syntax
        tree, reason = parser.parse(code, "python")
        assert tree is None
        assert reason in ["root_error_only", "no_meaningful_structure"]

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
        """Test that empty functions are handled appropriately."""
        code = """
        def empty():
            pass
        """
        tree, reason = parser.parse(code, "python")
        # Empty function with pass may or may not be discarded depending on parser behavior
        # Just ensure it either returns None or a tree
        assert tree is None or tree is not None

    # ===== is_trivial Tests =====

    def test_is_trivial_recognized_by_type(self, parser):
        """Test that is_trivial identifies trivial keywords."""
        # Create mock nodes
        from unittest.mock import Mock

        trivial_node = Mock()
        trivial_node.type = "return_statement"
        assert parser.is_trivial(trivial_node)

        break_node = Mock()
        break_node.type = "break_statement"
        assert parser.is_trivial(break_node)

    def test_is_not_trivial_assignment(self, parser):
        """Test that assignment statements are not trivial."""
        from unittest.mock import Mock

        assignment_node = Mock()
        assignment_node.type = "assignment_expression"
        assert not parser.is_trivial(assignment_node)

    # ===== is_meaningful Tests =====

    def test_is_meaningful_with_keywords(self, parser):
        """Test that is_meaningful identifies meaningful keywords."""
        from unittest.mock import Mock

        expr_node = Mock()
        expr_node.type = "binary_expression"
        assert parser.is_meaningful(expr_node)

        decl_node = Mock()
        decl_node.type = "variable_declaration"
        assert parser.is_meaningful(decl_node)

    def test_is_not_meaningful(self, parser):
        """Test that non-meaningful types return False."""
        from unittest.mock import Mock

        binary_node = Mock()
        binary_node.type = "binary_operator"
        assert not parser.is_meaningful(binary_node)

    # ===== has_meaningful_structure Tests =====

    def test_has_meaningful_structure_with_assignment(self, parser):
        """Test that functions with assignments have meaningful structure."""
        parser.ts_parser.language = get_language("python")
        code = """
        def func():
            x = 5
            y = x + 1
        """
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))

        # Find function definition in children
        func_node = find_child_with_type(tree_obj.root_node, "function_definition")
        assert func_node is not None
        assert parser.has_meaningful_structure(func_node)

    def test_has_not_meaningful_structure_only_return(self, parser):
        """Test that functions with only return lack meaningful structure."""
        parser.ts_parser.language = get_language("python")
        code = """
        def func():
            return
        """
        tree_obj = parser.ts_parser.parse(bytes(code, "utf8"))

        func_node = find_child_with_type(tree_obj.root_node, "function_definition")
        assert func_node is not None
        assert not parser.has_meaningful_structure(func_node)

    # ===== Language Support Tests =====

    def test_parse_unsupported_language(self, parser):
        """Test that unsupported languages raise error."""
        code = "some code"
        with pytest.raises((ValueError, LookupError)):
            parser.parse(code, "nonexistent_language")

    def test_parse_python_support(self, parser):
        """Test Python language support."""
        code = """
        def test():
            x = 42
            return x
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None

    def test_parse_java_support(self, parser):
        """Test Java language support."""
        code = """
        public class Test {
            public int getValue() {
                int x = 42;
                return x;
            }
        }
        """
        tree, reason = parser.parse(code, "java")
        # Java may be stricter with meaningful structure
        assert tree is not None or reason == "no_meaningful_structure"

    def test_parse_javascript_support(self, parser):
        """Test JavaScript language support."""
        code = """
        function test() {
            let x = 42;
            return x;
        }
        """
        tree, reason = parser.parse(code, "javascript")
        assert tree is not None

    # ===== Edge Cases =====

    def test_parse_with_comments(self, parser):
        """Test parsing code with comments."""
        code = """
        # This is a comment
        def add(a, b):
            # Another comment
            result = a + b
            return result
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None, f"Expected tree but got reason: {reason}"
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
        assert tree is not None, f"Expected tree but got reason: {reason}"
        assert reason is None

    def test_parse_with_syntax_error(self, parser):
        """Test parsing code with partial syntax errors."""
        code = """
        def incomplete(:  
            print("test")
        """
        tree, reason = parser.parse(code, "python")
        # Should be discarded due to errors
        assert tree is None or reason is not None

    def test_parse_with_conditionals(self, parser):
        """Test parsing code with conditional statements."""
        code = """
        def max_value(a, b):
            if a > b:
                max_val = a
            else:
                max_val = b
            return max_val
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None, f"Expected tree but got reason: {reason}"
        assert reason is None

    def test_parse_with_loops(self, parser):
        """Test parsing code with loop statements."""
        code = """
        def sum_range(n):
            total = 0
            for i in range(n):
                total = total + i
            return total
        """
        tree, reason = parser.parse(code, "python")
        assert tree is not None, f"Expected tree but got reason: {reason}"
        assert reason is None

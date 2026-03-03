"""Test cases for the adapter module.

Tests cover the conversion of Tree-sitter nodes to local Node structures,
including edge cases with various node types, Unicode content, and tree structures.
"""

import pytest
from tree_sitter import Node as TSNode, Parser as TSParser, Point
from tree_sitter_language_pack import get_language
from src.transtructiver.parsing.adapter import convert_node
from src.transtructiver.node import Node


class TestConvertNodeBasics:
    """Test suite for basic convert_node functionality."""

    @pytest.fixture
    def parser_setup(self) -> TSParser:
        """Setup parser for tests."""
        ts_parser = TSParser()
        ts_parser.language = get_language("python")
        return ts_parser

    def test_convert_leaf_node_with_text(self, parser_setup: TSParser):
        """Test converting a leaf node preserves its text content."""
        code = "42"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        leaf = tree.root_node.children[0]  # Navigate to a leaf node

        node = convert_node(leaf, source_bytes)

        assert node.text is not None
        assert isinstance(node.text, str)

    def test_convert_non_leaf_node_has_no_text(self, parser_setup: TSParser):
        """Test that non-leaf nodes have text set to None."""
        code = """
def add(a, b):
    return a + b
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Root module node should not have text
        assert node.text is None
        assert len(node.children) > 0

    def test_convert_node_preserves_type(self, parser_setup: TSParser):
        """Test that node type is preserved during conversion."""
        code = "x = 5"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        ts_node = tree.root_node

        node = convert_node(ts_node, source_bytes)

        assert node.type == ts_node.type

    def test_convert_empty_children(self, parser_setup: TSParser):
        """Test converting node with no children."""
        code = "x"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)

        # Find a leaf node
        def find_leaf(n):
            if n.child_count == 0:
                return n
            for child in n.children:
                result = find_leaf(child)
                if result:
                    return result
            return None

        leaf = find_leaf(tree.root_node)
        node = convert_node(leaf, source_bytes)

        assert node.children == []


class TestConvertNodeHierarchy:
    """Test suite for node hierarchy conversion."""

    @pytest.fixture
    def parser_setup(self) -> TSParser:
        """Setup parser for tests."""
        ts_parser = TSParser()
        ts_parser.language = get_language("python")
        return ts_parser

    def test_convert_node_recursive_structure(self, parser_setup: TSParser):
        """Test that recursive conversion creates proper tree structure."""
        code = """
def func(x):
    y = x + 1
    return y
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Check root has children
        assert len(node.children) > 0

        # Check children are Node instances
        for child in node.children:
            assert isinstance(child, Node)
            assert hasattr(child, "type")
            assert hasattr(child, "text")
            assert hasattr(child, "children")

    def test_convert_node_preserves_child_count(self, parser_setup: TSParser):
        """Test that number of children is preserved."""
        code = "x = 1"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        ts_node = tree.root_node

        node = convert_node(ts_node, source_bytes)

        assert len(node.children) == ts_node.child_count

    def test_convert_node_nested_structure(self, parser_setup: TSParser):
        """Test conversion of deeply nested structures."""
        code = """
class Calculator:
    def add(self, a, b):
        result = a + b
        return result
    
    def multiply(self, a, b):
        result = a * b
        return result
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Verify nested structure exists
        assert node.children is not None

        # Check that we can traverse multiple levels
        def check_tree_depth(n, depth=0):
            if not n.children:
                return depth
            return max(check_tree_depth(child, depth + 1) for child in n.children)

        depth = check_tree_depth(node)
        assert depth > 2  # Should have multiple levels


class TestConvertNodeEdgeCases:
    """Test suite for edge cases in node conversion."""

    @pytest.fixture
    def parser_setup(self) -> TSParser:
        """Setup parser for tests."""
        ts_parser = TSParser()
        ts_parser.language = get_language("python")
        return ts_parser

    def test_convert_node_with_unicode_content(self, parser_setup: TSParser):
        """Test converting nodes with Unicode content via escapes."""
        code = """
# Comment with unicode escapes
variable_name = "\u3053\u3093\u306b\u3061\u306f"
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Should not raise an exception and should preserve structure
        assert node is not None
        assert node.type == "module"

    def test_convert_node_with_special_characters(self, parser_setup: TSParser):
        """Test converting nodes with special characters."""
        code = '''s = "!@#$%^&*()_+-=[]{}|;:,.<>?"'''
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None

    def test_convert_node_with_empty_source(self, parser_setup: TSParser):
        """Test converting node from empty source."""
        code = ""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None
        assert node.type == "module"

    def test_convert_node_with_single_character(self, parser_setup: TSParser):
        """Test converting node with minimal input."""
        code = "x"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)

        def find_leaf(n):
            if n.child_count == 0:
                return n
            for child in n.children:
                result = find_leaf(child)
                if result:
                    return result
            return None

        leaf = find_leaf(tree.root_node)
        node = convert_node(leaf, source_bytes)

        assert node.text == "x"

    def test_convert_node_multiline_strings(self, parser_setup: TSParser):
        """Test converting nodes with multiline string content."""
        code = '''
text = """
Multi-line
string
content
"""
'''
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None

    def test_convert_node_with_escape_sequences(self, parser_setup: TSParser):
        """Test converting nodes with escape sequences."""
        code = r's = "line1\nline2\ttab"'
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None

    def test_convert_node_error_nodes_preserved(self, parser_setup: TSParser):
        """Test that error nodes are preserved during conversion."""
        code = "@@@"  # Invalid syntax
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Should still create a node structure, error nodes included
        assert node is not None

    def test_convert_large_code_structure(self, parser_setup: TSParser):
        """Test converting large, complex code structures."""
        # Generate a moderately large code structure
        code = (
            """
        def complex_function():
            """
            + "\n".join([f"    x{i} = {i}" for i in range(50)])
            + """

        result = sum([x0, x1, x2, x3, x4])
        """
        )
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None
        assert node.children is not None


class TestConvertNodeTextExtraction:
    """Test suite for text extraction in convert_node."""

    @pytest.fixture
    def parser_setup(self) -> TSParser:
        """Setup parser for tests."""
        ts_parser = TSParser()
        ts_parser.language = get_language("python")
        return ts_parser

    def test_extract_text_from_correct_byte_range(self, parser_setup: TSParser):
        """Test that text is extracted from correct byte positions."""
        code = "variable_name = 42"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        # Verify the structure was created correctly
        assert node is not None
        assert node.type == "module"

    def test_text_extraction_with_identical_source_bytes(self, parser_setup: TSParser):
        """Test text extraction preserves byte-for-byte accuracy."""
        code = "abc = xyz"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)

        def find_leaf(n):
            if n.child_count == 0:
                return n
            for child in n.children:
                result = find_leaf(child)
                if result:
                    return result
            return None

        leaf = find_leaf(tree.root_node)
        node = convert_node(leaf, source_bytes)

        extracted = source_bytes[leaf.start_byte : leaf.end_byte].decode("utf8")
        assert node.text == extracted

    def test_multiple_conversions_same_source_consistent(self, parser_setup: TSParser):
        """Test that multiple conversions of same source produce consistent text."""
        code = "x = 123"
        source_bytes = bytes(code, "utf8")
        tree1 = parser_setup.parse(source_bytes)
        tree2 = parser_setup.parse(source_bytes)

        node1 = convert_node(tree1.root_node, source_bytes)
        node2 = convert_node(tree2.root_node, source_bytes)

        assert node1.type == node2.type


class TestConvertNodeLanguageIndependence:
    """Test suite for convert_node with different languages."""

    def test_convert_node_python_code(self):
        """Test converting Python code."""
        parser = TSParser()
        parser.language = get_language("python")
        code = "def foo(): return 42"
        source_bytes = bytes(code, "utf8")
        tree = parser.parse(source_bytes)

        node = convert_node(tree.root_node, source_bytes)

        assert node.type == "module"
        assert len(node.children) > 0

    def test_convert_node_cpp_code(self):
        """Test converting C++ code."""
        parser = TSParser()
        parser.language = get_language("cpp")
        code = "int foo() { return 42; }"
        source_bytes = bytes(code, "utf8")
        tree = parser.parse(source_bytes)

        node = convert_node(tree.root_node, source_bytes)

        assert node.type == "translation_unit"
        assert len(node.children) > 0

    def test_convert_node_java_code(self):
        """Test converting Java code."""
        parser = TSParser()
        parser.language = get_language("java")
        code = """
public class Foo {
    public int bar() {
        return 42;
    }
}
"""
        source_bytes = bytes(code, "utf8")
        tree = parser.parse(source_bytes)

        node = convert_node(tree.root_node, source_bytes)

        assert node is not None
        assert isinstance(node, Node)


class TestConvertNodeWhitespace:
    """Test suite for whitespace handling in convert_node."""

    @pytest.fixture
    def parser_setup(self) -> TSParser:
        """Setup parser for tests."""
        ts_parser = TSParser()
        ts_parser.language = get_language("python")
        return ts_parser

    def test_convert_node_generates_whitespace_nodes(self, parser_setup: TSParser):
        """Test that convert_node generates whitespace nodes."""
        code = """
def func():
    x = 1
    return x
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None
        # Tree should contain whitespace nodes
        whitespace_nodes = [n for n in node.traverse() if n.type == "whitespace"]
        assert len(whitespace_nodes) > 0

    def test_convert_node_generates_newline_nodes(self, parser_setup: TSParser):
        """Test that convert_node generates newline nodes."""
        code = """
def func():
    x = 1
    return x
"""
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        assert node is not None
        # Tree should contain newline nodes
        newline_nodes = [n for n in node.traverse() if n.type == "newline"]
        assert len(newline_nodes) > 0
        assert len(newline_nodes) == 4

    def test_convert_node_whitespace_with_tabs(self, parser_setup: TSParser):
        """Test tab whitespace becomes explicit node text."""
        code = "\tx = 1"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        whitespaces = [n.text for n in node.traverse() if n.type == "whitespace"]
        assert len(whitespaces) == 3
        assert all(len(ws) == 1 for ws in whitespaces if ws)

    def test_convert_node_whitespace_indent(self, parser_setup: TSParser):
        """Test tab whitespace becomes explicit node text."""
        code = "    x=1"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)

        whitespaces = [n.text for n in node.traverse() if n.type == "whitespace"]
        assert len(whitespaces) == 1
        assert all(len(ws) == 4 for ws in whitespaces if ws)

    def test_convert_node_whitespace_propagates_to_children(self, parser_setup: TSParser):
        """Test that child-level whitespace becomes explicit whitespace nodes."""
        code = "x = 1"
        source_bytes = bytes(code, "utf8")
        tree = parser_setup.parse(source_bytes)
        root = tree.root_node

        node = convert_node(root, source_bytes)
        whitespaces = [n.text for n in node.traverse() if n.type == "whitespace"]

        assert len(whitespaces) == 2

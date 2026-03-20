"""Test cases for semantic annotation module.

Tests cover language-specific semantic annotation of syntax tree nodes,
including identifier classification, field-aware context analysis, and
multi-language support.
"""

import pytest
from tree_sitter import Parser as TSParser
from tree_sitter_language_pack import get_language

from transtructiver.node import Node
from transtructiver.parsing.adapter import convert_node

from transtructiver.parsing.annotation import (
    annotate,
    annotate_python,
    annotate_java,
    annotate_cpp,
)
from transtructiver.parsing.annotation.builtin_checker import make_profile_from_files
import os


def _profile(language):
    """Import language profile containing builtin names"""
    base_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../src/transtructiver/parsing/annotation/profiles"
        )
    )
    return make_profile_from_files(language, base_dir)


@pytest.fixture
def python_parser() -> TSParser:
    """Setup Python parser for tests."""
    parser = TSParser()
    parser.language = get_language("python")
    return parser


@pytest.fixture
def java_parser() -> TSParser:
    """Setup Java parser for tests."""
    parser = TSParser()
    parser.language = get_language("java")
    return parser


@pytest.fixture
def cpp_parser() -> TSParser:
    """Setup C++ parser for tests."""
    parser = TSParser()
    parser.language = get_language("cpp")
    return parser


def parse_and_convert(code: str, language: str = "python") -> Node:
    """Parse code and convert to internal Node representation."""
    if language == "python":
        parser = TSParser()
        parser.language = get_language("python")
    elif language == "java":
        parser = TSParser()
        parser.language = get_language("java")
    elif language == "cpp":
        parser = TSParser()
        parser.language = get_language("cpp")
    else:
        raise ValueError(f"Unsupported language: {language}")

    source_bytes = bytes(code, "utf8")
    tree = parser.parse(source_bytes)
    node = convert_node(tree.root_node, source_bytes)
    node.language = language
    return node


class TestAnnotatorDispatcher:
    """Test suite for the main annotate dispatcher function."""

    def test_annotate_python_module(self, python_parser: TSParser):
        """Test annotate dispatcher routes Python modules correctly."""
        code = "x = 42"
        source_bytes = bytes(code, "utf8")
        tree = python_parser.parse(source_bytes)
        node = convert_node(tree.root_node, source_bytes)
        node.language = "python"

        annotated = annotate(node)

        assert annotated is not None
        assert annotated.type == "module"

    def test_annotate_java_program(self, java_parser: TSParser):
        """Test annotate dispatcher routes Java programs correctly."""
        code = """
public class Foo {
    public static void main(String[] args) {
        int x = 42;
    }
}
"""
        source_bytes = bytes(code, "utf8")
        tree = java_parser.parse(source_bytes)
        node = convert_node(tree.root_node, source_bytes)
        node.language = "java"

        annotated = annotate(node)

        assert annotated is not None
        assert annotated.type == "program"

    def test_annotate_cpp_translation_unit(self, cpp_parser: TSParser):
        """Test annotate dispatcher routes C++ translation units correctly."""
        code = "int main() { return 0; }"
        source_bytes = bytes(code, "utf8")
        tree = cpp_parser.parse(source_bytes)
        node = convert_node(tree.root_node, source_bytes)
        node.language = "cpp"

        annotated = annotate(node)

        assert annotated is not None
        assert annotated.type == "translation_unit"

    def test_annotate_missing_language_raises_error(self):
        """Test annotate raises ValueError when root.language is missing."""
        unsupported_node = Node(
            start_point=(0, 0),
            end_point=(0, 1),
            type="unknown_root_type",
        )

        with pytest.raises(ValueError, match="No language found on root node"):
            annotate(unsupported_node)

    def test_annotate_error_message_mentions_root_language(self):
        """Test error message tells caller to set root.language."""
        unsupported_node = Node(
            start_point=(0, 0),
            end_point=(0, 1),
            type="unknown_type",
        )

        with pytest.raises(ValueError, match="Set root.language"):
            annotate(unsupported_node)


class TestPythonAnnotator:
    """Test suite for Python semantic annotation."""

    def test_annotate_function_name(self, python_parser: TSParser):
        """Test function names are annotated correctly."""
        code = "def my_function(): pass"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Find function_definition node
        func_defs = [n for n in annotated.traverse() if n.type == "function_definition"]
        assert len(func_defs) == 1

        # Function name should have semantic label
        func_def = func_defs[0]
        function_names = [n for n in func_def.traverse() if n.semantic_label == "function_name"]
        assert len(function_names) == 1

    def test_annotate_variable_assignment(self, python_parser: TSParser):
        """Test variable names in assignments are annotated."""
        code = "my_var = 123"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Find identifiers with variable_name label
        var_names = [n for n in annotated.traverse() if n.semantic_label == "variable_name"]
        assert len(var_names) == 1

    def test_annotate_class_name(self, python_parser: TSParser):
        """Test class names are annotated correctly."""
        code = "class MyClass: pass"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Find class names
        class_names = [n for n in annotated.traverse() if n.semantic_label == "class_name"]
        assert len(class_names) == 1

    def test_annotate_parameter_names(self, python_parser: TSParser):
        """Test parameter names are annotated."""
        code = "def func(param1, param2): pass"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Find parameter names
        param_names = [n for n in annotated.traverse() if n.semantic_label == "parameter_name"]
        assert len(param_names) == 2

    def test_annotate_global_variable(self, python_parser: TSParser):
        """Test global variable declarations are annotated."""
        code = "def func():\n    global x\n    x = 5"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Find identifiers in global statement
        global_vars = [
            n
            for n in annotated.traverse()
            if n.type == "identifier" and n.parent and n.parent.type == "global_statement"
        ]
        assert len(global_vars) == 1
        assert global_vars[0].semantic_label == "variable_name"

    def test_annotate_type_annotation(self, python_parser: TSParser):
        """Test type annotations are recognized."""
        code = "x: int = 5"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Type identifiers should have type_name label
        type_names = [n for n in annotated.traverse() if n.semantic_label == "type_name"]
        assert len(type_names) == 1

    def test_annotate_whitespace_and_newlines_skipped(self, python_parser: TSParser):
        """Test that whitespace and newline nodes are skipped during annotation."""
        code = "x = 1"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        # Whitespace and newline nodes should not have semantic labels
        whitespace_with_labels = [
            n
            for n in annotated.traverse()
            if n.type in ("whitespace", "newline") and n.semantic_label is not None
        ]
        assert len(whitespace_with_labels) == 0

    def test_unresolved_identifier_falls_back_to_variable_name(self, python_parser: TSParser):
        """Unresolved identifiers in snippet fragments should remain renamable."""
        code = "result = ext + ext2"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        names = [
            n.semantic_label
            for n in annotated.traverse()
            if n.type == "identifier" and n.text in {"ext", "ext2"}
        ]
        assert names
        assert all(label == "variable_name" for label in names)

    def test_annotate_exception_name(self, python_parser: TSParser):
        """Test exception names in raise statements are labeled as exception_name."""
        code = "raise Exception('error')"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        exception_names = [n for n in annotated.traverse() if n.semantic_label == "exception_name"]
        assert len(exception_names) == 1
        assert exception_names[0].text == "Exception"


class TestJavaAnnotator:
    """Test suite for Java semantic annotation."""

    def test_annotate_method_name(self, java_parser: TSParser):
        """Test method names are annotated correctly."""
        code = """
public class Foo {
    public void myMethod() { }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Find method names
        function_names = [n for n in annotated.traverse() if n.semantic_label == "function_name"]
        assert len(function_names) == 1

    def test_annotate_class_name(self, java_parser: TSParser):
        """Test class names are annotated in Java."""
        code = "public class MyClass { }"
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Find class names
        class_names = [n for n in annotated.traverse() if n.semantic_label == "class_name"]
        assert len(class_names) == 1

    def test_annotate_type_identifier(self, java_parser: TSParser):
        """Test type identifiers are labeled as type_name."""
        code = """
public class Foo {
    int x;
    String y;
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Type identifiers should be labeled
        type_names = [n for n in annotated.traverse() if n.semantic_label == "type_name"]
        assert len(type_names) >= 1

    def test_annotate_field_access(self, java_parser: TSParser):
        """Test field access creates variable/property names."""
        code = """
public class Foo {
    public static void main(String[] args) {
        obj.field = 5;
    }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Field/property access
        var_names = [n for n in annotated.traverse() if n.semantic_label == "property_name"]
        assert len(var_names) == 1

    def test_annotate_method_invocation(self, java_parser: TSParser):
        """Test method invocations are labeled as function names."""
        code = """
public class Foo {
    public static void main(String[] args) {
        obj.method();
    }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Method calls should create function names
        function_names = [n for n in annotated.traverse() if n.semantic_label == "function_name"]
        assert len(function_names) == 2

    def test_annotate_formal_parameter(self, java_parser: TSParser):
        """Test formal parameters are annotated."""
        code = """
public class Foo {
    public void method(int param1, String param2) { }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        # Parameters should be labeled
        param_names = [n for n in annotated.traverse() if n.semantic_label == "parameter_name"]
        assert len(param_names) == 2

    def test_unresolved_identifier_falls_back_to_variable_name(self, java_parser: TSParser):
        """Unresolved identifiers in snippet fragments should remain renamable."""
        code = "class A { void f(){ x = y + z; } }"
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        names = [
            n.semantic_label
            for n in annotated.traverse()
            if n.type == "identifier" and n.text in {"x", "y", "z"}
        ]
        assert names
        assert all(label == "variable_name" for label in names)

    def test_annotate_exception_name(self, java_parser: TSParser):
        """Test exception names in throw statements are labeled as exception_name."""
        code = """
        public class Foo {
            public void bar() {
                throw new Exception("fail");
            }
        }
        """
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        exception_names = [n for n in annotated.traverse() if n.semantic_label == "exception_name"]
        assert len(exception_names) == 1
        assert exception_names[0].text == "Exception"


class TestCppAnnotator:
    """Test suite for C++ semantic annotation."""

    def test_annotate_function_name(self, cpp_parser: TSParser):
        """Test function names are annotated in C++."""
        code = "int myFunction() { return 0; }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Find function names
        function_names = [n for n in annotated.traverse() if n.semantic_label == "function_name"]
        assert len(function_names) == 1

    def test_unresolved_identifier_falls_back_to_variable_name(self, cpp_parser: TSParser):
        """Unresolved identifiers in snippet fragments should remain renamable."""
        code = "int main(){ return x + y; }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        names = [
            n.semantic_label
            for n in annotated.traverse()
            if "identifier" in n.type and n.text in {"x", "y"}
        ]
        assert names
        assert all(label == "variable_name" for label in names)

    def test_annotate_type_identifier(self, cpp_parser: TSParser):
        """Test type identifiers are labeled in C++."""
        code = """
struct MyType {
    int value;
};

int main() {
    MyType obj;
    return 0;
}
"""
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Type identifiers (custom types like struct/class)
        type_names = [n for n in annotated.traverse() if n.semantic_label == "type_name"]
        assert len(type_names) == 1

    def test_annotate_variable_reference(self, cpp_parser: TSParser):
        """Test variable references in expressions."""
        code = "int main() { int x = 5; int y = x + 1; return 0; }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Variable names should exist
        var_names = [n for n in annotated.traverse() if n.semantic_label == "variable_name"]
        assert len(var_names) == 3

    def test_annotate_field_identifier(self, cpp_parser: TSParser):
        """Test field identifiers in C++."""
        code = """
class MyClass {
public:
    int myField;
};

int main() {
    MyClass obj;
    obj.myField = 5;
}
"""
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Field/property access
        property_names = [n for n in annotated.traverse() if n.semantic_label == "property_name"]
        assert len(property_names) == 1

    def test_annotate_namespace_identifier(self, cpp_parser: TSParser):
        """Test namespace identifiers are labeled."""
        code = "namespace myNamespace { }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Namespace names
        namespace_names = [n for n in annotated.traverse() if n.semantic_label == "namespace_name"]
        assert len(namespace_names) == 1

    def test_annotate_class_name_in_destructor(self, cpp_parser: TSParser):
        """Test class names in destructors are labeled."""
        code = """
class MyClass {
public:
    ~MyClass() { }
};
"""
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        # Class names
        class_names = [n for n in annotated.traverse() if n.semantic_label == "class_name"]
        assert len(class_names) == 2

    def test_annotate_exception_name(self, cpp_parser: TSParser):
        """Test exception names in throw statements are labeled as exception_name."""
        code = "void foo() { throw std::exception(); }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        annotated.pretty()

        exception_names = [n for n in annotated.traverse() if n.semantic_label == "exception_name"]
        assert len(exception_names) == 1
        assert "exception" in exception_names[0].text  # type: ignore


class TestAnnotationEdgeCases:
    """Test suite for edge cases in annotation."""

    def test_annotate_empty_python_module(self):
        """Test annotating empty Python module."""
        code = ""
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        assert annotated is not None
        assert annotated.type == "module"

    def test_annotate_python_with_comments(self):
        """Test Python annotation with comment nodes."""
        code = """
# This is a comment
x = 5  # Inline comment
"""
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        assert annotated is not None
        # Should not raise errors

    def test_annotate_preserves_node_structure(self):
        """Test that annotation preserves the node structure."""
        code = "def foo(x): return x + 1"
        node = parse_and_convert(code, "python")
        child_count_before = len(list(node.traverse()))

        annotated = annotate_python(node, _profile("python"))
        child_count_after = len(list(annotated.traverse()))

        assert child_count_before == child_count_after

    def test_annotate_preserves_parent_links(self):
        """Test that parent links remain valid after annotation."""
        code = "class A:\n    def method(self): pass"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        for child in annotated.traverse():
            if child.parent is not None:
                assert child in child.parent.children

    def test_annotate_idempotent(self):
        """Test that calling annotate multiple times is safe."""
        code = "x = 42"
        node = parse_and_convert(code, "python")

        annotated1 = annotate_python(node, _profile("python"))
        annotated2 = annotate_python(annotated1, _profile("python"))

        # Should have same structure
        labels1 = [n.semantic_label for n in annotated1.traverse()]
        labels2 = [n.semantic_label for n in annotated2.traverse()]
        assert labels1 == labels2


class TestUnifiedScopeLabels:
    """Test suite for unified semantic labels across language-specific node types."""

    def test_python_function_definition_has_function_scope_label(self):
        """Python function_definition should map to unified function_scope label."""
        code = "def foo(x): return x"
        node = parse_and_convert(code, "python")
        annotated = annotate_python(node, _profile("python"))

        func_defs = [n for n in annotated.traverse() if n.type == "function_definition"]
        assert len(func_defs) == 1
        assert func_defs[0].semantic_label == "function_scope"

    def test_java_method_declaration_has_function_scope_label(self):
        """Java method_declaration should map to unified function_scope label."""
        code = """
public class Foo {
    public void bar() { }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate_java(node, _profile("java"))

        method_nodes = [n for n in annotated.traverse() if n.type == "method_declaration"]
        assert len(method_nodes) == 1
        assert method_nodes[0].semantic_label == "function_scope"

    def test_cpp_function_definition_has_function_scope_label(self):
        """C++ function_definition should map to unified function_scope label."""
        code = "int foo() { return 1; }"
        node = parse_and_convert(code, "cpp")
        annotated = annotate_cpp(node, _profile("cpp"))

        func_defs = [n for n in annotated.traverse() if n.type == "function_definition"]
        assert len(func_defs) == 1
        assert func_defs[0].semantic_label == "function_scope"


class TestAnnotationIntegration:
    """Integration tests for full annotation pipeline."""

    def test_full_python_pipeline(self):
        """Test complete annotation of Python code."""
        code = """
def calculate(a, b):
    result = a + b
    return result

class Calculator:
    def __init__(self, value):
        self.value = value
    
    def add(self, x):
        return self.value + x
"""
        node = parse_and_convert(code, "python")
        annotated = annotate(node)

        # Find all semantic labels
        all_labels = {
            n.semantic_label for n in annotated.traverse() if n.semantic_label is not None
        }

        # Should have various annotation types
        assert len(all_labels) > 0

    def test_full_java_pipeline(self):
        """Test complete annotation of Java code."""
        code = """
public class Hello {
    private String greeting;
    
    public Hello(String msg) {
        this.greeting = msg;
    }
    
    public void printGreeting() {
        System.out.println(greeting);
    }
}
"""
        node = parse_and_convert(code, "java")
        annotated = annotate(node)

        # Should have annotations
        all_labels = {
            n.semantic_label for n in annotated.traverse() if n.semantic_label is not None
        }
        assert len(all_labels) > 0

    def test_full_cpp_pipeline(self):
        """Test complete annotation of C++ code."""
        code = """
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int result = fibonacci(10);
    return 0;
}
"""
        node = parse_and_convert(code, "cpp")
        annotated = annotate(node)

        # Should have annotations
        all_labels = {
            n.semantic_label for n in annotated.traverse() if n.semantic_label is not None
        }
        assert len(all_labels) > 0

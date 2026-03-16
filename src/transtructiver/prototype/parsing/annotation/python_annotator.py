"""Python semantic annotator.

Adds semantic labels to Python syntax tree nodes using field-aware context analysis.
Annotations enable identifier classification (variable_name, function_name, etc.)
based on declaration context and usage patterns. Works in conjunction with the
unified label system defined in annotator.py to provide consistent classification
across Python, Java, and C++ code.

Annotation approach:
- Post-order traversal (children before parent) ensures scope context is available
- Field names on nodes indicate role in parent structure (e.g., 'function' field
  in a call expression indicates the function being called)
- Special handling for attribute expressions and nested class definitions
"""

from ...node import Node
from .annotator import ROOT_TO_LANGUAGE, NAMING_ANCESTOR_LABELS, get_unified_type_label
from .annotation_utils import walk


def _annotate_node(node: Node) -> None:
    """Annotate a single Python node with semantic labels.

    Processes one node at a time; traversal is handled externally by
    :func:`annotate_python` using :func:`~.annotation_utils.walk`.

    Args:
        node (Node): The node to annotate.
    """
    if node.type in ("whitespace", "newline"):
        return

    if node.type == "comment":
        node.semantic_label = "line_comment"
        return

    parent = node.parent
    if parent is None:
        if node.type in ROOT_TO_LANGUAGE:
            node.semantic_label = "root"
        return

    if node.type == "string" and parent.type in ("module", "block"):
        for child in node.children:
            if child.type in {"string_start", "string_end"} and child.text in ('"""', "'''"):
                node.semantic_label = "block_comment"
        return

    if node.type == "identifier":
        _annotate_identifier(node)

    _annotate_scope_types(node)


def _annotate_scope_types(node: Node) -> None:
    """Assign unified semantic labels for scope-like node types.

    Maps Python-specific scope node types to unified semantic labels that
    represent the same scoping behavior across different languages:
    - 'function_scope' for function definitions
    - 'class_scope' for class definitions
    - 'block_scope' for code blocks
    - 'loop_scope' for loop constructs

    Args:
        node (Node): The node to check and label if it's a scope type.
    """
    unified_label = get_unified_type_label(node.type)
    if unified_label is not None:
        node.semantic_label = unified_label
    return


def _annotate_identifier(node: Node) -> None:
    """Annotate Python identifiers based on declaration and usage context.

    Routes identifier annotation through multiple specialized handlers:
    1. Direct field-based patterns (function, object fields)
    2. Naming ancestor context (function_definition, parameters, etc.)
    3. Assignment context (left-hand side of assignments)
    4. Attribute expressions (property vs. method calls)

    Args:
        node (Node): An identifier node to annotate with a semantic label.
    """
    parent = node.parent
    if parent is None:
        return

    if node.field == "function":
        node.semantic_label = "function_name"
        return

    if node.field == "object":
        node.semantic_label = "variable_name"
        return

    if _try_label_from_naming_ancestor(node):
        return

    if parent.type in ("assignment", "augmented_assignment"):
        if node.field == "left":
            node.semantic_label = "variable_name"
            return

    if parent.type == "attribute":
        _annotate_attribute_identifier(node, parent)


def _annotate_attribute_identifier(node: Node, parent: Node) -> None:
    """Annotate identifiers within attribute expressions.

    Distinguishes between method calls and property access within attribute
    expressions. An attribute on the right side of `.` is labeled:
    - 'function_name' if accessed within a call expression
    - 'property_name' otherwise

    Args:
        node (Node): The identifier node (the right side of `.`)
        parent (Node): The parent attribute node
    """
    if node.field == "attribute" and parent.parent:
        node.semantic_label = "function_name" if parent.parent.type == "call" else "property_name"
    else:
        node.semantic_label = "variable_name"


def _try_label_from_naming_ancestor(node: Node) -> bool:
    """Try to label a node based on its naming ancestor.

    Searches for the nearest ancestor node that provides semantic meaning
    to the identifier (e.g., a function_definition, parameter declaration,
    or class_definition). If found, uses the naming ancestor's type to
    determine the appropriate semantic label.

    Args:
        node (Node): The identifier node to potentially label.

    Returns:
        bool: True if the node was successfully labeled, False otherwise.
    """
    naming_ancestor = _find_nearest_naming_ancestor(node)
    if naming_ancestor is not None:
        label = _label_for_naming_ancestor(node, naming_ancestor)
        if label is not None:
            node.semantic_label = label
            return True
    return False


def _find_nearest_naming_ancestor(node: Node) -> Node | None:
    """Find the nearest ancestor that gives semantic meaning to identifiers.

    Searches up the parent chain for declaration context nodes such as:
    - function_definition (function name)
    - parameters (parameter name)
    - class_definition (class name)
    - global_statement, nonlocal_statement (variable context)
    - argument_list (class name if in superclasses field, else variable)
    - type (type name)

    Args:
        node (Node): The identifier node whose context to find.

    Returns:
        Node | None: The nearest naming ancestor, or None if no relevant
            context is found.
    """
    parent = node.parent
    if parent is None:
        return None

    if parent.type in NAMING_ANCESTOR_LABELS["python"]:
        return parent

    return None


def _label_for_naming_ancestor(node: Node, naming_ancestor: Node) -> str | None:
    """Map a naming ancestor type to a semantic label.

    Determines the semantic label for an identifier based on its declaration
    context. Handles special cases like superclass context in argument lists.

    Args:
        node (Node): The identifier node being labeled.
        naming_ancestor (Node): The ancestor node providing context.

    Returns:
        str | None: The semantic label (variable_name, parameter_name,
            function_name, class_name, type_name), or None if the context
            is not recognized.
    """
    if naming_ancestor.type == "argument_list":
        return (
            "class_name" if node.parent and node.parent.field == "superclasses" else "variable_name"
        )
    return NAMING_ANCESTOR_LABELS["python"].get(naming_ancestor.type)


def annotate_python(node: Node) -> Node:
    """Annotate a Python syntax tree with semantic labels.

    Main entry point for Python semantic annotation. Processes the entire
    tree in post-order (children before parent) using :func:`~.annotation_utils.walk`,
    assigning semantic labels to all identifiers and scope-defining nodes
    based on Python-specific syntax patterns.

    Args:
        node (Node): The root of the Python syntax tree (module node).

    Returns:
        Node: The same tree with semantic_label attributes set throughout.
    """
    for n in walk(node):
        _annotate_node(n)
    return node

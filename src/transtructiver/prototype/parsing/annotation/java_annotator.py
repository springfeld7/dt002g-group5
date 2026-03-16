"""Java semantic annotator.

Adds semantic labels to Java syntax tree nodes using field-aware context analysis.
Annotations enable identifier classification (variable_name, function_name, etc.)
based on declaration context and usage patterns. Works in conjunction with the
unified label system defined in annotator.py to provide consistent classification
across Python, Java, and C++ code.

Annotation approach:
- Post-order traversal (children before parent) ensures scope context is available
- Distinguishes between type_identifier and regular identifier for type safety
- Handles method references, field access, and method invocations with operator analysis
"""

from ...node import Node
from .annotator import ROOT_TO_LANGUAGE, NAMING_ANCESTOR_LABELS, get_unified_type_label
from .annotation_utils import walk


def _annotate_node(node: Node) -> None:
    """Annotate a single Java node with semantic labels.

    Processes one node at a time; traversal is handled externally by
    :func:`annotate_java` using :func:`~.annotation_utils.walk`.

    Args:
        node (Node): The node to annotate.
    """
    if node.type in ("whitespace", "newline"):
        return

    if node.type == "line_comment":
        node.semantic_label = "line_comment"
        return

    if node.type == "block_comment":
        node.semantic_label = "block_comment"
        return

    parent = node.parent
    if parent is None:
        if node.type in ROOT_TO_LANGUAGE:
            node.semantic_label = "root"
        return

    if node.type in ("identifier", "type_identifier"):
        _annotate_identifier(node)

    _annotate_scope_types(node)


def _annotate_scope_types(node: Node) -> None:
    """Assign unified semantic labels for scope-like node types.

    Maps Java-specific scope node types to unified semantic labels that
    represent the same scoping behavior across different languages:
    - 'function_scope' for method and constructor declarations
    - 'class_scope' for class and interface declarations
    - 'block_scope' for code blocks and class bodies
    - 'loop_scope' for loop constructs

    Args:
        node (Node): The node to check and label if it's a scope type.
    """
    unified_label = get_unified_type_label(node.type)
    if unified_label is not None:
        node.semantic_label = unified_label


def _annotate_identifier(node: Node) -> None:
    """Annotate Java identifiers and type identifiers based on field context.

    Routes identifier annotation through multiple specialized handlers:
    1. Type identifier classification (type_name label)
    2. Naming ancestor context (method_declaration, formal_parameter, etc.)
    3. Method reference handling with :: operator
    4. Field access and method invocation with . operator analysis

    Args:
        node (Node): An identifier or type_identifier node to annotate.
    """
    parent = node.parent
    if parent is None:
        return

    if node.type == "type_identifier":
        node.semantic_label = "type_name"
        return

    if _try_label_from_naming_ancestor(node):
        return

    if parent.type == "method_reference" and _is_right_side_of_operator(node, parent, "::"):
        node.semantic_label = "function_name"
        return

    if parent.type in ("field_access", "method_invocation"):
        if _has_operator(parent, "."):
            if _is_right_side_of_operator(node, parent, "."):
                node.semantic_label = (
                    "property_name" if parent.type == "field_access" else "function_name"
                )
            else:
                node.semantic_label = "variable_name"
        else:
            node.semantic_label = "function_name"
        return


def _try_label_from_naming_ancestor(node: Node) -> bool:
    """Try to label a node based on its naming ancestor.

    Searches for the nearest ancestor node that provides semantic meaning
    to the identifier (e.g., a method_declaration, formal_parameter, or
    class_declaration). If found, uses the naming ancestor's type to
    determine the appropriate semantic label.

    Args:
        node (Node): The identifier node to potentially label.

    Returns:
        bool: True if the node was successfully labeled, False otherwise.
    """
    naming_ancestor = _find_nearest_naming_ancestor(node)
    if naming_ancestor is not None:
        label = _label_for_naming_ancestor(naming_ancestor.type)
        if label is not None:
            node.semantic_label = label
            return True
    return False


def _find_nearest_naming_ancestor(node: Node) -> Node | None:
    """Find the nearest ancestor that gives semantic meaning to identifiers.

    Searches up the parent chain for declaration context nodes such as:
    - method_declaration (function name)
    - formal_parameter (parameter name)
    - variable_declarator (variable name)
    - class_declaration, interface_declaration (class/type name)
    - constructor_declaration (class name)
    - enum_declaration (enum type identifier)

    Args:
        node (Node): The identifier node whose context to find.

    Returns:
        Node | None: The nearest naming ancestor, or None if no relevant
            context is found.
    """
    current = node.parent
    while current is not None:
        if current.type in NAMING_ANCESTOR_LABELS["java"]:
            return current
        if _is_naming_boundary(current):
            return None
        current = current.parent

    return None


def _is_naming_boundary(node: Node) -> bool:
    """Return True when traversing further would leave declaration context.

    Identifies nodes that represent boundaries beyond which declaration
    context is lost. Prevents incorrect labeling of identifiers in nested
    contexts like loop bodies or nested expressions.

    Args:
        node (Node): The node to check.

    Returns:
        bool: True if the node marks a boundary, False otherwise.
    """
    if node.type in {"program", "block", "class_body"}:
        return True

    return node.type.endswith("_statement") or node.type.endswith("_expression")


def _label_for_naming_ancestor(ancestor_type: str) -> str | None:
    """Map a naming ancestor type to a semantic label.

    Determines the semantic label for an identifier based on its declaration
    ancestor type within the Java context.

    Args:
        ancestor_type (str): The ancestor node type to map.

    Returns:
        str | None: The semantic label (variable_name, parameter_name,
            function_name, class_name, etc.), or None if not recognized.
    """
    # return get_naming_ancestor_label("java", ancestor_type)
    return NAMING_ANCESTOR_LABELS["java"].get(ancestor_type)


def _has_operator(parent: Node, operator: str) -> bool:
    """Check whether an operator token exists among direct children.

    Searches the direct children of a parent node for a specific operator
    token string. Used to disambiguate expressions like field_access
    vs. method_invocation based on presence of `.` or `::` operators.

    Args:
        parent (Node): The parent node to search.
        operator (str): The operator string to look for (e.g., ".", "::").

    Returns:
        bool: True if the operator exists among direct children.
    """
    return any(child.text == operator for child in parent.children)


def _is_right_side_of_operator(node: Node, parent: Node, operator: str) -> bool:
    """Check if the identifier is on the right side of an operator.

    Returns True if the node appears after the first operator occurrence.

    Determines whether an identifier appears after a specific operator in
    a parent node. For example, in 'obj.method', 'method' is right of the `.`
    operator and 'obj' is left of it.

    Args:
        node (Node): The identifier node to check.
        parent (Node): The parent expression node.
        operator (str): The operator to search for (e.g., ".", "::").

    Returns:
        bool: True if the node is to the right of the first operator occurrence.
    """
    found_operator = False
    for child in parent.children:
        if child.text == operator:
            found_operator = True

        elif found_operator and child == node:
            return True

    return False


def annotate_java(node: Node) -> Node:
    """Annotate a Java syntax tree with semantic labels.

    Main entry point for Java semantic annotation. Processes the entire tree
    in post-order (children before parent) using :func:`~.annotation_utils.walk`,
    assigning semantic labels to all identifiers and scope-defining nodes
    based on Java-specific syntax patterns.

    Args:
        node (Node): The root of the Java syntax tree (program node).

    Returns:
        Node: The same tree with semantic_label attributes set throughout.
    """
    for n in walk(node):
        _annotate_node(n)
    return node

"""C++ semantic annotator.

Adds semantic labels to C++ syntax tree nodes using field-aware context analysis.
Annotations enable identifier classification (variable_name, function_name, etc.)
based on declaration context and usage patterns. Works in conjunction with the
unified label system defined in annotator.py to provide consistent classification
across Python, Java, and C++ code.

Annotation approach:
- Post-order traversal (children before parent) ensures scope context is available
- Handles multiple identifier types: identifier, field_identifier, type_identifier, namespace_identifier
- Special handling for destructor names, method references, and qualified identifiers
"""

from ...node import Node
from .annotator import _ROOT_TO_LANGUAGE, get_naming_ancestor_label, get_unified_type_label


def _annotate_node(node: Node) -> None:
    """Recursively annotate a C++ node and its children with semantic labels.

    Uses post-order traversal (children before parent) to ensure scope-related
    nodes are identified before processing their children's context. This allows
    accurate labeling of identifiers based on their enclosing namespaces and scopes.

    Args:
        node (Node): The node to annotate. All children are annotated recursively.
    """
    for child in node.children:
        _annotate_node(child)

    if node.type in ("whitespace", "newline"):
        return
    
    parent = node.parent
    if parent is None:
        if node.type in _ROOT_TO_LANGUAGE:
            node.semantic_label = "root"
        return

    if "identifier" in node.type:
        _annotate_identifier(node)

    _annotate_scope_types(node)


def _annotate_scope_types(node: Node) -> None:
    """Assign unified semantic labels for scope-like node types.

    Maps C++-specific scope node types to unified semantic labels that
    represent the same scoping behavior across different languages:
    - 'function_scope' for function declarations and definitions
    - 'class_scope' for class, struct, and enum definitions
    - 'block_scope' for compound statements and code blocks
    - 'loop_scope' for loop constructs

    Args:
        node (Node): The node to check and label if it's a scope type.
    """
    unified_label = get_unified_type_label(node.type)
    if unified_label is not None:
        node.semantic_label = unified_label


def _annotate_identifier(node: Node) -> None:
    """Annotate C++ identifiers and type identifiers based on field context.

    Routes identifier annotation through multiple specialized handlers:
    1. Namespace identifier classification
    2. Field identifier handling (property vs. function)
    3. Destructor name detection
    4. Declaration context via naming ancestors
    5. Qualified identifier fallback
    6. Field expression and expression context handling
    7. Type identifier classification

    Args:
        node (Node): An identifier-type node to annotate with a semantic label.
    """
    parent = node.parent
    if parent is None:
        return
    
    if node.type == "namespace_identifier":
        node.semantic_label = "namespace_name"
        return
    
    if node.type == "field_identifier":
        if node.field == "field":
            node.semantic_label = "property_name"
            return
        elif (parent.type == "field_expression" and 
            parent.parent and parent.parent.type == "call_expression" and
            parent.field == "function"):
            node.semantic_label = "function_name"
            return
        else:
            node.semantic_label = "variable_name"
            return
    
    if parent.type == "call_expression" and node.field == "function":
        node.semantic_label = "function_name"
        return
    
    # Destructor names: class name in destructor
    if parent.type == "destructor_name":
        node.semantic_label = "class_name"
        return
    
    # Declaration names and declarators: use ancestor context
    if node.field in ("name", "declarator") or parent.field == "declarator":
        if _try_label_from_naming_ancestor(node):
            return
        # Qualified identifier names fall back to variable reference
        if parent.type == "qualified_identifier":
            node.semantic_label = "variable_name"
            return
    
    # Field expression argument (the object being accessed)
    if node.field == "argument" and parent.type == "field_expression":
        node.semantic_label = "variable_name"
        return
    
    # Variable references in expressions (only for identifiers not yet labeled)
    if node.type == "identifier" and node.semantic_label is None:
        if parent.type in (
            "binary_expression",
            "update_expression",
            "unary_expression",
            "assignment_expression",
            "subscript_expression",
            "argument_list",
            "return_statement",
            "condition_clause",
            "for_range_loop",
            "init_statement",
            "expression_statement",
            "compound_statement",
            "delete_expression",
        ):
            node.semantic_label = "variable_name"
            return
    
    # Fallback: generic type identifiers that are not declaration names
    if node.type == "type_identifier" and node.semantic_label is None:
        node.semantic_label = "type_name"


def _try_label_from_naming_ancestor(node: Node) -> bool:
    """Try to label a node based on its naming ancestor.

    Searches for the nearest ancestor node that provides semantic meaning
    to the identifier (e.g., a function_definition, class_specifier, or
    parameter_declaration). If found, uses the naming ancestor's type to
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
    """Find the nearest ancestor that gives semantic meaning to a `name` field.

    Searches up the parent chain for declaration context nodes such as:
    - function_declarator, function_definition (function name)
    - parameter_declaration (parameter name)
    - init_declarator, field_declaration (variable name)
    - class_specifier, struct_specifier (class/struct name)
    - enum_specifier (enum type name)
    - enumerator (enum constant name)
    - namespace_definition (namespace name)
    - type_alias_declaration (type alias name)
    - preproc_def (macro name)

    Args:
        node (Node): The identifier node whose context to find.

    Returns:
        Node | None: The nearest naming ancestor, or None if no relevant
            context is found.
    """
    naming_context_types = {
        "function_declarator",
        "function_definition",
        "parameter_declaration",
        "init_declarator",
        "class_specifier",
        "struct_specifier",
        "enum_specifier",
        "enumerator",
        "namespace_definition",
        "type_alias_declaration",
        "field_declaration",
        "preproc_def",
    }

    current = node.parent
    while current is not None:
        if current.type in naming_context_types:
            return current
        current = current.parent

    return None


def _label_for_naming_ancestor(ancestor_type: str) -> str | None:
    """Map a naming ancestor type to a semantic label.

    Determines the semantic label for an identifier based on its declaration
    ancestor type within the C++ context.

    Args:
        ancestor_type (str): The ancestor node type to map.

    Returns:
        str | None: The semantic label (variable_name, parameter_name,
            function_name, class_name, namespace_name, type_name, etc.),
            or None if not recognized.
    """
    return get_naming_ancestor_label("cpp", ancestor_type)


def annotate_cpp(node: Node) -> Node:
    """Annotate a C++ syntax tree with semantic labels.

    Main entry point for C++ semantic annotation. Recursively processes
    the entire tree, assigning semantic labels to all identifier-type nodes
    and scope-defining nodes based on C++-specific syntax patterns.

    Args:
        node (Node): The root of the C++ syntax tree (translation_unit node).

    Returns:
        Node: The same tree with semantic_label attributes set throughout.
    """
    _annotate_node(node)
    return node

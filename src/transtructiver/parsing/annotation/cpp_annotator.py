"""C++ semantic annotator.

Adds semantic labels to C++ syntax tree nodes using field-aware context.
"""

from ...node import Node


def _annotate_node(node: Node) -> None:
    """Recursively annotate a C++ node and its children with semantic labels."""
    for child in node.children:
        _annotate_node(child)

    if node.type in ("whitespace", "newline"):
        return
    
    parent = node.parent
    if parent is None:
        return

    if "identifier" in node.type:
        _annotate_identifier(node)


def _annotate_identifier(node: Node) -> None:
    """Annotate C++ identifiers and type identifiers based on field context."""
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
    """Try to label a node based on its naming ancestor. Returns True if labeled."""
    naming_ancestor = _find_nearest_naming_ancestor(node)
    if naming_ancestor is not None:
        label = _label_for_naming_ancestor(naming_ancestor.type)
        if label is not None:
            node.semantic_label = label
            return True
    return False


def _find_nearest_naming_ancestor(node: Node) -> Node | None:
    """Find the nearest ancestor that gives semantic meaning to a `name` field."""
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
    """Map a naming ancestor type to a semantic label."""
    labels = {
        **dict.fromkeys(["function_declarator", "function_definition"], "function_name"),
        **dict.fromkeys(["class_specifier", "struct_specifier", "enum_specifier"], "class_name"),
        **dict.fromkeys(["init_declarator", "field_declaration", "enumerator", "preproc_def"], "variable_name"),
        "parameter_declaration": "parameter_name",
        "namespace_definition": "namespace_name",
        "type_alias_declaration": "type_name",
    }
    return labels.get(ancestor_type)


def annotate_cpp(node: Node) -> Node:
    """Annotate a C++ syntax tree with semantic labels."""
    _annotate_node(node)
    return node

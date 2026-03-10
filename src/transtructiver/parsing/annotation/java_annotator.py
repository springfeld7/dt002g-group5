"""Java semantic annotator.

Adds semantic labels to Java syntax tree nodes using field-aware context.
"""

from ...node import Node


def _annotate_node(node: Node) -> None:
    """Recursively annotate a Java node and its children with semantic labels."""
    for child in node.children:
        _annotate_node(child)

    if node.type in ("whitespace", "newline"):
        return

    parent = node.parent
    if parent is None:
        return

    if node.type in ("identifier", "type_identifier"):
        _annotate_identifier(node)


def _annotate_identifier(node: Node) -> None:
    """Annotate Java identifiers and type identifiers based on field context."""
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
                node.semantic_label = "property_name" if parent.type == "field_access" else "function_name"
            else:
                node.semantic_label = "variable_name"
        else:
            node.semantic_label = "function_name"
        return


def _try_label_from_naming_ancestor(node: Node) -> bool:
    """Try to label a node based on its naming ancestor. Returns True if labeled."""
    if node.field not in ("name", "declarator"):
        return False

    naming_ancestor = _find_nearest_naming_ancestor(node)
    if naming_ancestor is not None:
        label = _label_for_naming_ancestor(naming_ancestor.type)
        if label is not None:
            node.semantic_label = label
            return True
    return False


def _find_nearest_naming_ancestor(node: Node) -> Node | None:
    """Find the nearest ancestor that gives semantic meaning to identifiers."""
    naming_context_types = {
        "method_declaration",
        "annotation_type_element_declaration",
        "formal_parameter",
        "variable_declarator",
        "class_declaration",
        "constructor_declaration",
        "compact_constructor_declaration",
        "record_declaration",
        "interface_declaration",
        "annotation_type_declaration",
        "enum_declaration",
    }

    current = node.parent
    while current is not None:
        if current.type in naming_context_types:
            return current
        if _is_naming_boundary(current):
            return None
        current = current.parent

    return None


def _is_naming_boundary(node: Node) -> bool:
    """Return True when traversing further would leave declaration context."""
    if node.type in {"program", "block", "class_body"}:
        return True

    return node.type.endswith("_statement") or node.type.endswith("_expression")


def _label_for_naming_ancestor(ancestor_type: str) -> str | None:
    """Map a naming ancestor type to a semantic label."""
    labels = {
        **dict.fromkeys(["method_declaration", "annotation_type_element_declaration"], "function_name"),
        "formal_parameter": "parameter_name",
        "variable_declarator": "variable_name",
        **dict.fromkeys(
            [
                "class_declaration",
                "constructor_declaration",
                "compact_constructor_declaration",
                "record_declaration",
                "interface_declaration",
                "annotation_type_declaration",
                "enum_declaration",
            ],
            "class_name"
        ),
    }
    return labels.get(ancestor_type)


def _has_operator(parent: Node, operator: str) -> bool:
    """Check whether an operator token exists among direct children."""
    return any(child.text == operator for child in parent.children)


def _is_right_side_of_operator(node: Node, parent: Node, operator: str) -> bool:
    """Check if the identifier is on the right side of an operator.

    Returns True if the node appears after the first operator occurrence.
    """
    found_operator = False
    for child in parent.children:
        if child.text == operator:
            found_operator = True

        elif found_operator and child == node:
            return True

    return False


def annotate_java(node: Node) -> Node:
    """Annotate a Java syntax tree with semantic labels."""
    _annotate_node(node)
    return node

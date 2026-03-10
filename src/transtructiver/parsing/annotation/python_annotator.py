"""Python semantic annotator.

Adds semantic labels to Python syntax tree nodes using field-aware context.
"""

from ...node import Node


def _annotate_node(node: Node) -> None:
    """Recursively annotate a Python node and its children with semantic labels."""
    for child in node.children:
        _annotate_node(child)

    if node.type in ("whitespace", "newline"):
        return

    parent = node.parent
    if parent is None:
        return

    if node.type == "identifier":
        _annotate_identifier(node)


def _annotate_identifier(node: Node) -> None:
    """Annotate Python identifiers based on declaration and usage context."""
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
    """Annotate identifiers within attribute expressions."""
    if node.field == "attribute" and parent.parent:
        node.semantic_label = "function_name" if parent.parent.type == "call" else "property_name"
    else:
        node.semantic_label = "variable_name"


def _try_label_from_naming_ancestor(node: Node) -> bool:
    """Try to label a node based on its naming ancestor. Returns True if labeled."""
    naming_ancestor = _find_nearest_naming_ancestor(node)
    if naming_ancestor is not None:
        label = _label_for_naming_ancestor(node, naming_ancestor)
        if label is not None:
            node.semantic_label = label
            return True
    return False


def _find_nearest_naming_ancestor(node: Node) -> Node | None:
    """Find the nearest ancestor that gives semantic meaning to identifiers."""
    naming_context_types = {
        "function_definition",
        "parameters",
        "typed_parameter",
        "default_parameter",
        "typed_default_parameter",
        "class_definition",
        "global_statement",
        "nonlocal_statement",
        "argument_list",
        "type",
    }

    parent = node.parent
    if parent is None:
        return None

    if parent.type in naming_context_types:
        return parent

    return None


def _label_for_naming_ancestor(node: Node, naming_ancestor: Node) -> str | None:
    """Map a naming ancestor type to a semantic label."""
    labels = {
        **dict.fromkeys(["global_statement", "nonlocal_statement", "arguments"], "variable_name"),
        **dict.fromkeys(["parameters", "typed_parameter", "default_parameter", "typed_default_parameter"], "parameter_name"),
        "function_definition": "function_name",
        "class_definition": "class_name",
        "argument_list": "class_name" if node.parent and node.parent.field == "superclasses" else "variable_name",
        "type": "type_name",
    }

    return labels.get(naming_ancestor.type)


def annotate_python(node: Node) -> Node:
    """Annotate a Python syntax tree with semantic labels."""
    _annotate_node(node)
    return node

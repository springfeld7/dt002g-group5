"""Semantic annotation dispatcher and unified label definitions.

This module provides the central registry for semantic labels used across
all language annotators (Python, Java, C++). It dispatches nodes to the
appropriate language-specific annotator based on the root node type, and
defines unified semantic labels for consistent identifier classification
across different programming languages.

Key concepts:
- Unified semantic labels enable consistent treatment of equivalent constructs
  across languages (e.g., Python's function_definition, Java's method_declaration,
  and C++'s function_definition all map to 'function_scope')
- Language-specific naming ancestor labels map declaration contexts to semantic
  categories (e.g., 'parameter_name', 'class_name', 'function_name')
- Lazy-loaded annotators prevent circular imports
"""

from collections.abc import Callable

from ...node import Node


# Maps root node types (language-specific syntax tree roots) to language names.
# This determines which language-specific annotator to use.
ROOT_TO_LANGUAGE = {
    "module": "python",
    "program": "java",
    "translation_unit": "cpp",
}


# Cross-language semantic labels for scope-defining node types.
# Maps language-specific node type names to unified semantic labels that represent
# similar constructs across Python, Java, and C++. This enables the mutation engine
# and other tools to treat equivalent structures uniformly regardless of language.
#
# Examples:
#   - Python's and C++'s 'function_definition' and Java's 'method_declaration' all map to 'function_scope'
#   - Blocks/compounds map to 'block_scope' for scope tracking
UNIFIED_TYPE_LABELS = {
    **dict.fromkeys(
        [
            "function_definition",
            "method_declaration",
            "constructor_declaration",
            "compact_constructor_declaration",
            "lambda",
        ],
        "function_scope",
    ),
    **dict.fromkeys(
        [
            "class_definition",
            "class_declaration",
            "class_specifier",
            "struct_specifier",
            "interface_declaration",
            "record_declaration",
            "enum_declaration",
            "annotation_type_declaration",
        ],
        "class_scope",
    ),
    **dict.fromkeys(["block", "compound_statement", "class_body"], "block_scope"),
    **dict.fromkeys(["for_statement", "while_statement", "for_range_loop"], "loop_scope"),
}


# Language-specific semantic labels for declaration ancestors.
# Maps (language, ancestor_node_type) pairs to semantic labels that classify
# the identifiers within those contexts. For example, an identifier within a
# 'formal_parameter' context in Java gets labeled 'parameter_name'.
#
# Used to annotate identifiers based on their declaration context, enabling
# mutation rules to selectively target specific identifier categories.
NAMING_ANCESTOR_LABELS = {
    "python": {
        **dict.fromkeys(
            ["global_statement", "nonlocal_statement", "argument_list"], "variable_name"
        ),
        **dict.fromkeys(
            ["parameters", "typed_parameter", "default_parameter", "typed_default_parameter"],
            "parameter_name",
        ),
        "function_definition": "function_name",
        "class_definition": "class_name",
        "type": "type_name",
    },
    "java": {
        **dict.fromkeys(
            ["method_declaration", "annotation_type_element_declaration"], "function_name"
        ),
        **dict.fromkeys(["formal_parameters"], "parameter_name"),
        **dict.fromkeys(["variable_declarator", "argument_list"], "variable_name"),
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
            "class_name",
        ),
    },
    "cpp": {
        **dict.fromkeys(["function_declarator", "function_definition"], "function_name"),
        **dict.fromkeys(["class_specifier", "struct_specifier", "enum_specifier"], "class_name"),
        **dict.fromkeys(
            ["init_declarator", "field_declaration", "enumerator", "preproc_def"], "variable_name"
        ),
        "parameter_declaration": "parameter_name",
        "namespace_definition": "namespace_name",
        "type_alias_declaration": "type_name",
    },
}


def get_unified_type_label(node_type: str) -> str | None:
    """Return the cross-language semantic label for a structural node type.

    Maps language-specific node types (like 'method_declaration') to unified
    semantic labels (like 'function_scope') that represent the same concept
    across Python, Java, and C++.

    Args:
        node_type (str): The language-specific node type to look up.

    Returns:
        str | None: The unified semantic label ('function_scope', 'class_scope',
            'block_scope', 'loop_scope'), or None if the node type is not a
            recognized scope-defining construct.

    Example:
        >>> get_unified_type_label('method_declaration')
        'function_scope'
        >>> get_unified_type_label('class_definition')
        'class_scope'
        >>> get_unified_type_label('identifier')
        None
    """
    return UNIFIED_TYPE_LABELS.get(node_type)


# Registry mapping language keys to their annotate functions.
# Populated on first use by _ensure_registry_populated() to avoid
# circular imports with the language-specific annotator modules.
_ANNOTATOR_REGISTRY: dict[str, Callable[[Node], Node]] = {}


def _ensure_registry_populated() -> None:
    """Populate the annotator registry on first use.

    Uses lazy imports to prevent circular dependencies between this dispatcher
    module and the language-specific annotator modules.
    """
    if _ANNOTATOR_REGISTRY:
        return
    from .python_annotator import annotate_python
    from .java_annotator import annotate_java
    from .cpp_annotator import annotate_cpp

    # Register all built-in annotators together after the lazy imports succeed.
    _ANNOTATOR_REGISTRY.update(
        {
            "python": annotate_python,
            "java": annotate_java,
            "cpp": annotate_cpp,
        }
    )


def annotate(root: Node) -> Node:
    """Annotate a node tree with semantic labels based on language.

    Main entry point for semantic annotation. Determines the programming
    language from the root node type and dispatches to the registered
    language-specific annotator. Each identifier node receives a
    semantic_label describing its declaration context (e.g., variable_name,
    function_name, parameter_name).

    Args:
        root (Node): The root node of the syntax tree to annotate. Should be a
            language-specific root type (module, program, or translation_unit).

    Returns:
        Node: The same root node with semantic_label attributes set on all
            identifier and scope-defining nodes throughout the tree.

    Raises:
        ValueError: If the root node type is not recognized as a supported
            language root (not 'module', 'program', or 'translation_unit').
    """
    language = ROOT_TO_LANGUAGE.get(root.type)
    if language is None:
        raise ValueError(
            f"No annotator found for root node type '{root.type}'. "
            f"Supported types: {list(ROOT_TO_LANGUAGE.keys())}"
        )

    _ensure_registry_populated()
    return _ANNOTATOR_REGISTRY[language](root)

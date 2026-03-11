"""Private appendage heuristics for RenameIdentifiersRule.

This module is intentionally internal to the rename-identifiers rule.
It derives type-aware suffix tokens from declaration context and formats
renamed identifier text according to language-specific naming conventions.
"""

from typing import Callable

from ....node import Node
from ....parsing.annotation.annotator import NAMING_ANCESTOR_LABELS
from ....parsing.annotation.annotation_utils import meaningful_children


# Canonical suffix map that collapses equivalent type names to shared tokens.
_TYPE_SUFFIXES = {
    **dict.fromkeys(["list"], "list"),
    **dict.fromkeys(["tuple"], "tuple"),
    **dict.fromkeys(["dict", "dictionary"], "dict"),
    **dict.fromkeys(["set"], "set"),
    **dict.fromkeys(["str", "string"], "str"),
    **dict.fromkeys(["int", "integer", "float", "double", "number"], "num"),
    **dict.fromkeys(["bool", "boolean"], "flag"),
}

# Semantic-only fallback when no concrete type hint can be inferred.
_SEMANTIC_FALLBACK_SUFFIXES = {
    "function_name": "fn",
    "class_name": "cls",
    "property_name": "attr",
}


def _ancestor_types_for_label(label: str) -> set[str]:
    """Return ancestor node types that map to a semantic naming label.

    Args:
        label: Semantic label to reverse-map (for example ``variable_name``).

    Returns:
        A set of ancestor node types associated with the given label.
    """
    return {
        node_type
        for language_map in NAMING_ANCESTOR_LABELS.values()
        for node_type, semantic_label in language_map.items()
        if semantic_label == label
    }


def _build_appendage_name(node: Node, language: str) -> str:
    """Build renamed identifier text for a node.

    Args:
        node: Identifier node being renamed.
        language: Language key resolved from CST root.

    Returns:
        The formatted identifier text after suffix inference.
    """
    if not node.text:
        return ""

    suffix = _infer_suffix(node)
    if node.text.endswith(f"_{suffix}"):
        return node.text

    return _format_new_name(node.text, suffix, language)


def _infer_from_type_nodes(node: Node) -> str | None:
    """Scan the parent and grandparent 'type' fields for a canonical suffix.

    Only searches if the parent node type is a known declaration ancestor for
    the node's semantic label.

    Args:
        node: Identifier node with populated ``semantic_label`` and ``parent``.

    Returns:
        Canonical suffix token if a type annotation is found, otherwise None.
    """
    parent = node.parent
    if parent is None or not node.semantic_label:
        return None

    # Restrict type inference to declaration-shaped contexts for this label.
    if parent.type not in _ancestor_types_for_label(node.semantic_label):
        return None

    # First prefer an inline type child on the declaration itself.
    for child in meaningful_children(parent):
        if child is not node and child.field == "type":
            result = _suffix_from_type_node(child)
            if result is not None:
                return result

    # Then try sibling type nodes from the declaration's parent context.
    if parent.parent is not None:
        for sibling in parent.parent.children:
            if sibling is not parent and sibling.field == "type":
                result = _suffix_from_type_node(sibling)
                if result is not None:
                    return result

    return None


def _infer_from_semantic_label(node: Node) -> str | None:
    """Return a suffix based solely on the node's semantic label.

    Args:
        node: Identifier node with a populated ``semantic_label``.

    Returns:
        Canonical suffix token if the label maps to one, otherwise None.
    """
    return _SEMANTIC_FALLBACK_SUFFIXES.get(node.semantic_label or "")


def _infer_suffix(node: Node) -> str:
    """Infer a semantic or type suffix token.

    Delegates first to type-node scanning and falls back to the label-based
    heuristic when no type annotation is present.

    Args:
        node: Identifier node context used for inference.

    Returns:
        Canonical suffix token (for example ``list`` or ``fn``), or an empty
        string when no suffix can be inferred.
    """
    return _infer_from_type_nodes(node) or _infer_from_semantic_label(node) or ""


def _resolve_type_text(type_node: Node) -> str | None:
    """Return the best available text for a type annotation node.

    Tries the node's own text first, then the first child with text.

    Args:
        type_node: Node representing a type annotation.

    Returns:
        Non-empty text string, or None if nothing is available.
    """
    if type_node.text:
        return type_node.text
    for nested in type_node.children:
        if nested.text:
            return nested.text
    return None


def _extract_terminal_type(text: str, parent_type: str | None) -> str:
    """Return the most specific type name from a qualified type string.

    Strips namespace qualifiers, generic parameters, and package prefixes
    according to how the type appears in its parent context.

    Args:
        text: Lowercased type text.
        parent_type: The parent node type, used to choose a parsing strategy.

    Returns:
        The terminal (rightmost, most specific) type name.
    """
    normalized = text.strip()
    if not normalized:
        return ""

    # method_reference may include constructor/method tails (e.g., List::new).
    if parent_type == "method_reference":
        normalized = normalized.split("::", 1)[0]

    # Drop generic type arguments so List<String> resolves to List.
    if "<" in normalized:
        normalized = normalized.split("<", 1)[0]

    # Keep only the terminal type for qualified names like java.util.List.
    normalized = normalized.rsplit("::", 1)[-1].split(".")[-1]
    return normalized.strip()


def _match_type_suffix(lowered: str, terminal: str) -> str | None:
    """Map a terminal type name to a canonical suffix token.

    First tries an exact lookup, then falls back to substring scanning
    over all known type keys (longest key first to prefer more specific matches).

    Args:
        lowered: Full lowercased type text used for substring fallback.
        terminal: Most specific type name from the type string.

    Returns:
        Canonical suffix token if a match is found, otherwise None.
    """
    # Fast path: exact terminal type match.
    exact = _TYPE_SUFFIXES.get(terminal)
    if exact is not None:
        return exact

    # Fallback: substring scan for composite types (e.g., Optional[List[int]]).
    for key in sorted(_TYPE_SUFFIXES.keys(), key=len, reverse=True):
        if key in lowered:
            return _TYPE_SUFFIXES[key]
    return None


def _suffix_from_type_node(type_node: Node) -> str | None:
    """Derive a canonical suffix token from a type annotation node.

    Delegates text extraction to :func:`_resolve_type_text`, terminal
    parsing to :func:`_extract_terminal_type`, and lookup to
    :func:`_match_type_suffix`.

    Args:
        type_node: Node representing a type annotation or type-like context.

    Returns:
        Canonical suffix token if resolvable, otherwise None.
    """
    type_text = _resolve_type_text(type_node)
    if not type_text:
        return None
    parent_type = type_node.parent.type if type_node.parent else None
    terminal = _extract_terminal_type(type_text.lower(), parent_type)
    return _match_type_suffix(type_text.lower(), terminal)


# Explicit per-language name formatters.
# New languages can be added here without modifying _format_new_name.
_LANGUAGE_FORMATTERS: dict[str, Callable[[str, str], str]] = {
    "python": lambda text, suffix: f"{text}_{suffix}",
}


def _format_generic(text: str, suffix: str) -> str:
    """Format an identifier using generic (non-Python) camelCase-suffix style."""
    return text + suffix.capitalize()


def _format_new_name(text: str, suffix: str, language: str) -> str:
    """Format a new identifier from base ``text``, ``suffix``, and ``language``.

    Args:
        text: Original identifier text.
        suffix: Canonical suffix token.
        language: Language key resolved from root.

    Returns:
        Formatted identifier text according to current language rules.

    Notes:
        Python formatting uses snake_case suffixes, while non-Python
        languages use camelCase-suffix via :func:`_format_generic`.
        Both are registered in :data:`_LANGUAGE_FORMATTERS`.
    """
    # Preserve current behavior for empty/unknown formatting inputs.
    if not suffix or not language:
        return text + text[-1]

    # Dispatch via registry for explicit, extensible language formatting.
    return _LANGUAGE_FORMATTERS.get(language, _format_generic)(text, suffix)

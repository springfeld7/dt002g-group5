"""Parsing interface for producing a CST from source code.

This module defines a Parser class that produces a CST using Tree-sitter
and converts the resulting syntax tree into the project's Node structure.
"""

from tree_sitter import Node as TSNode
from tree_sitter import Parser as TSParser
from tree_sitter_language_pack import get_language, SupportedLanguage
from typing import cast
from .adapter import adapt
from ..node import Node

# Keywords used to identify nodes with meaningful code logic.
# These patterns match node types that represent substantive program constructs.
MEANINGFUL_NODE_TYPES = [
    "expression",
    "statement",
    "definition",
    "declaration",
    "assignment",
    "block",
    "suite",
    "lambda",
    "list_comprehension",
    "identifier",
    "call",
]

# Keywords used to identify nodes with trivial content.
# These patterns match node types that don't significantly contribute to code logic.
TRIVIAL_NODE_TYPES = [
    "return",
    "break",
    "continue",
    "empty",
    "comment",
]


class Parser:
    """Parser that produces a Concrete Syntax Tree (CST).

    The implementation uses Tree-sitter as the parsing backend and
    adapts the resulting tree into the local Node model. Provides methods
    for classifying nodes as meaningful/trivial and filtering parse trees
    based on code quality and structure.

    Attributes:
        ts_parser (TSParser): The underlying Tree-sitter parser instance.
    """

    def __init__(self):
        """Initialize the Parser with a new Tree-sitter parser instance.

        Sets up the base parser that will be configured with language-specific
        grammars during parse() calls.
        """
        self.ts_parser = TSParser()

    # ------------------------------------------------------------
    # Meaningful / trivial checks
    # ------------------------------------------------------------

    def is_trivial(self, node: TSNode) -> bool:
        """Check if a node represents trivial code.

        Trivial nodes are those that don't contribute meaningful logic,
        such as return statements without expressions, breaks, continues,
        empty statements, or comments.

        Args:
            node (TSNode): The Tree-sitter node to check.

        Returns:
            bool: True if the node type matches any trivial pattern.
        """
        return any(t in node.type for t in TRIVIAL_NODE_TYPES)

    def is_meaningful(self, node: TSNode) -> bool:
        """Check if a node represents meaningful code.

        Meaningful nodes contain substantive logic such as expressions,
        statements, definitions, declarations, assignments, blocks, or
        lambda expressions.

        Args:
            node (TSNode): The Tree-sitter node to check.

        Returns:
            bool: True if the node type matches any meaningful pattern.
        """
        return any(kw in node.type for kw in MEANINGFUL_NODE_TYPES)

    def has_meaningful_structure(self, node: TSNode) -> bool:
        """Check if a node contains meaningful structure in its body.

        This method searches for a body block (block, suite, or compound)
        within the node, then checks if that body contains any meaningful
        non-trivial children. If no body is found, it checks the node's
        direct children.

        Args:
            node (TSNode): The Tree-sitter node to analyze.

        Returns:
            bool: True if the node contains at least one meaningful,
                non-trivial child in its body or direct children.
        """
        body = None
        for child in node.children:
            if any(kw in child.type for kw in ["block", "suite", "compound"]):
                body = child
                break

        target = body if body else node

        for child in target.named_children:
            if (self.is_meaningful(child) and not self.is_trivial(child)) or (
                "return" in child.type and child.named_child_count > 0
            ):
                return True

        return False

    def should_discard(self, root: TSNode, source: str) -> str | None:
        """Determine if a parse tree should be discarded.

        Applies filtering logic to reject parse trees that don't contain
        useful code, such as empty sources, root-level errors, or code
        without meaningful structure.

        Args:
            root (TSNode): The root Tree-sitter node of the parse tree.
            source (str): The original source code string.

        Returns:
            str | None: A reason string if the tree should be discarded:
                - "empty_source": Source contains only whitespace
                - "no_children": Root has no child nodes
                - "root_error_only": All root children are error nodes
                - "no_meaningful_structure": No children have meaningful structure
                None if the tree should be kept.
        """
        if not source.strip():
            return "empty_source"

        if root.child_count < 1:
            return "no_children"

        if all(child.is_error for child in root.children):
            return "root_error_only"

        if any(self.has_meaningful_structure(child) for child in root.children):
            return None
        else:
            return "no_meaningful_structure"

    # ------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------

    def parse(self, code: str, language: str) -> tuple[Node, None] | tuple[None, str]:
        """Parse source code into a Concrete Syntax Tree (CST).

        Parses the provided source code using Tree-sitter, applies
        filtering logic, and converts the result into the project's Node
        structure.

        Args:
            code (str): The source code to parse.
            language (str): The programming language (e.g., "python", "java").

        Returns:
            tuple[Node, None] | tuple[None, str]: On success, returns
                (Node, None) where Node is the root of the CST. On failure,
                returns (None, reason) where reason is one of:
                - "invalid_utf8": Code contains invalid UTF-8
                - "empty_source": Source is empty or whitespace-only
                - "no_children": Parse tree has no children
                - "root_error_only": All children are parse errors
                - "no_meaningful_structure": Code lacks meaningful content

        Raises:
            ValueError: If the specified language is not supported.
        """
        try:
            ts_language = get_language(cast(SupportedLanguage, language.lower()))
        except LookupError:
            raise ValueError(f"Unsupported language: {language}")

        try:
            code.encode("utf-8")
        except UnicodeEncodeError:
            return None, "invalid_utf8"

        self.ts_parser.language = ts_language

        source_bytes = bytes(code, "utf8")
        source_tree = self.ts_parser.parse(source_bytes)
        root_node = source_tree.root_node
        # Discard logic
        reason = self.should_discard(root_node, code)
        if reason:
            return None, reason

        converted_tree = adapt(root_node, source_bytes)
        return converted_tree, None

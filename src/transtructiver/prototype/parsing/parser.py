"""Parsing interface for producing a CST from source code.

This module defines a Parser class that produces a CST using Tree-sitter
and converts the resulting syntax tree into the project's Node structure.
"""

from tree_sitter import Node as TSNode
from tree_sitter import Parser as TSParser
from tree_sitter_language_pack import get_language, SupportedLanguage
from typing import cast
from .adapter import convert_node


MEANINGFUL_NODE_TYPES = [
    "expression",
    "statement",
    "definition",
    "declaration",
    "assignment",
    "block",
    "suite",
]

TRIVIAL_NODE_TYPES = [
    "return",
    "break",
    "continue",
    "empty",
]


class Parser:
    """Parser that produces a Concrete Syntax Tree (CST).

    The implementation uses Tree-sitter as the parsing backend and
    adapts the resulting tree into the local Node model.
    """

    def __init__(self):
        self.ts_parser = TSParser()

    def is_trivial(self, node: TSNode):
        """Check if a node represents a trivial statement.

        Args:
            node (TSNode): Tree-sitter node to check.

        Returns:
            bool: True if node type matches any trivial statement pattern.
        """
        return any(t in node.type for t in TRIVIAL_NODE_TYPES)

    def is_meaningful(self, node: TSNode):
        """Check if a node represents a meaningful code structure.

        Args:
            node (TSNode): Tree-sitter node to check.

        Returns:
            bool: True if node type matches any meaningful structure pattern.
        """
        return any(kw in node.type for kw in MEANINGFUL_NODE_TYPES)

    def has_meaningful_structure(self, node: TSNode):
        """Determine if a node contains meaningful, non-trivial code structures.

        Looks for a body block (block/suite/compound) within the node, then checks
        if it contains at least one meaningful statement that isn't trivial.

        Args:
            node (TSNode): Tree-sitter node to analyze.

        Returns:
            bool: True if the node contains at least one meaningful, non-trivial statement.
        """
        # Check if body exists
        body = None
        for child in node.children:
            if any(kw in child.type for kw in ["block", "suite", "compound"]):
                body = child
                break

        # Set the target node
        target = body if body else node

        # Ensure target contains at least one meaningful non-trivial node
        for child in target.named_children:
            if self.is_meaningful(child) and not self.is_trivial(child):
                return True

        return False

    def should_discard(self, root: TSNode, source):
        """Determine if a parsed tree should be discarded based on quality criteria.

        Checks for various conditions that indicate the source code snippet is not
        suitable for further processing (e.g., empty, all errors, no meaningful content).

        Args:
            root (TSNode): The root Tree-sitter node of the parsed tree.
            source (str): The original source code string.

        Returns:
            str | None: A reason string if the tree should be discarded, None if valid.
                Possible reasons: "empty_source", "no_children", "root_error_only",
                "no_meaningful_structure".
        """
        if not source.strip():
            return "empty_source"

        if root.child_count < 1:
            return "no_children"

        # Get first node of the tree
        if all(child.is_error for child in root.children):
            return "root_error_only"

        if not any(self.has_meaningful_structure(child) for child in root.children):
            return "no_meaningful_structure"

        return None

    def parse(self, code: str, language: str):
        """Parse source code into a CST.

        Args:
            code (str): The source code to parse.
            language (str): A Tree-sitter language name supported by the
                language pack, e.g. "python".

        Returns:
            Node: The root of the parsed CST.
        """
        try:
            ts_language = get_language(cast(SupportedLanguage, language.lower()))
        except KeyError:
            raise ValueError(f"Unsupported language: {language}")

        # UTF-8 encoding check
        try:
            code.encode("utf-8")
        except UnicodeEncodeError:
            return None, "invalid_utf8"

        # Parse code with Tree-sitter
        self.ts_parser.language = ts_language

        source_bytes = bytes(code, "utf8")
        source_tree = self.ts_parser.parse(source_bytes)
        root_node = source_tree.root_node

        # Apply discard criteria
        reason = self.should_discard(root_node, code)
        if reason:
            return None, reason

        # Convert valid CST and return
        converted_tree = convert_node(root_node, source_bytes)
        return converted_tree, None

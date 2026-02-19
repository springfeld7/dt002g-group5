"""Parsing interface for producing a CST from source code.

This module defines a Parser class that produces a CST using Tree-sitter
and converts the resulting syntax tree into the project's Node structure.
"""

from tree_sitter import Parser as TSParser
from tree_sitter_language_pack import get_language, SupportedLanguage
from typing import cast
from .adapter import convert_node


class Parser:
    """Parser that produces a Concrete Syntax Tree (CST).

    The implementation uses Tree-sitter as the parsing backend and
    adapts the resulting tree into the local Node model.
    """

    def __init__(self):
        self.ts_parser = TSParser()

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
            ts_language = get_language(cast(SupportedLanguage, language))
        except KeyError:
            raise ValueError(f"Unsupported language: {language}")

        self.ts_parser.language = ts_language

        source_bytes = bytes(code, "utf8")
        source_tree = self.ts_parser.parse(source_bytes)

        converted_tree = convert_node(source_tree.root_node, source_bytes)
        return converted_tree

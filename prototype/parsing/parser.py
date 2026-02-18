"""Parsing interface for producing a CST from source code.

This module defines a Parser class that returns a CST from input code.
Currently it returns a mock CST for demonstration.
"""

from prototype.mock.mock_cst import cst


class Parser:
    """Parser that produces a Concrete Syntax Tree (CST).

    The current implementation is a stub that returns a predefined CST.
    This class is designed to be extended with a real parsing backend.
    """

    def __init__(self):
        """Initialize the Parser instance."""
        pass

    def parse(self, code: str):
        """Parse source code into a CST.

        Args:
            code (str): The source code to parse.

        Returns:
            Node: The root of the parsed CST.
        """
        return cst

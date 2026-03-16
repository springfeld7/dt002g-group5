"""Mock Concrete Syntax Tree (CST) for testing and demonstration.

This module provides a sample CST representing a simple Python function definition.
It's used for testing mutation rules and the mutation engine.

The sample CST represents the following Python code:
    def add(a, b):
        return a + b
"""

from ..node import Node

cst = Node(
    (0, 0),
    (1, 20),
    "module",
    children=[
        Node(
            (0, 0),
            (1, 20),
            "function_definition",
            children=[
                Node((0, 4), (0, 7), "identifier", text="add"),
                Node(
                    (0, 7),
                    (0, 13),
                    "parameters",
                    children=[
                        Node((0, 8), (0, 9), "identifier", text="a"),
                        Node((0, 11), (0, 12), "identifier", text="b"),
                    ],
                ),
                Node(
                    (0, 13),
                    (1, 20),
                    "block",
                    children=[
                        Node(
                            (1, 4),
                            (1, 20),
                            "return_statement",
                            children=[
                                Node(
                                    (1, 11),
                                    (1, 20),
                                    "binary_operator",
                                    children=[
                                        Node((1, 11), (1, 12), "identifier", text="a"),
                                        Node((1, 13), (1, 14), "operator", text="+"),
                                        Node((1, 15), (1, 16), "identifier", text="b"),
                                    ],
                                )
                            ],
                        )
                    ],
                ),
            ],
        )
    ],
)
